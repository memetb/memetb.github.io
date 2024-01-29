# Memet Bilgin's personal blog


## That time I nuked my root directory on a device in northern Canada

I was a co-founder and CTO of a company that specialized in industrial battery EMS systems that were deployed to oil-rigs. These assets were in unusually unreachable spots where a so-called "truck roll" cost was measured in tens of thousands and sometimes would take 7 hours to get to from places like Grand Prairie, Alberta.

As a result, that one time I nuked one of the linux embedded systems from under my feet, I engaged that badger mode and decided, come hell or high water, I was going to restore the device.

A few very fortunate design decisions I had taken early on in the design of our fleet helped me out. Our controls hardware consisted of 4 identical beaglebone devices who had the following properties:

1. the root partition was mounted read-only and was identical between each device
2. the devices were networked to each other in a private vlan


What follows is my lessons learned about how to recover from the dreaded `rm -rf /`. More on why or how I got there in another post.

## Assumptions, statements, notes...

1. do not, under any circumstance, let go of your active ssh session!!!
1. the ultimate goal should be to get access to `chmod`, `dd` and `nc`, which is then sufficient to bootstrap.
1. it is possible to paste escaped binary text directly into a `tty`. I previously (incorrectly) thought the only way to do this was via `base64`
1. there is a builtin `echo` command if you're already in a shell - this is different from the `echo` command which may no longer exist
1. it is a big challenge to dump binaries onto the crippled system and then be able to execute them: doing `echo -e "<ESCAPED BINARY>" > ./cp` leaves you with a `./cp` that doesn't have an execute bit set
1. you can do a poor man's `ls` by doing `for i in *; do echo $i; done`
1. `gcc -static` is your friend because there are no `.so` files anywhere (including `libc.so`). However, it produces very large files (large for manual copy pasting, that is)
1. build super minimal `C` programs that do a single thing (like chmod)
1. when things show up as "file not found", (like when calling `cp`), it's because an `.so` is missing. Best way to determine what `so`'s a binary requires are using `ldd $(which cp)` (on a live system)
1. having access to a live system of the same kind (e.g. armv7 or amd64) is crucial in maintaining sanity

Note: to escape text for binary pasting, use `xxd -p < netcat | sed 's/../\\x&/g' | awk '{printf $0}' > netcat.dump`

## Game plan

The following is what we're trying to achieve:
```bash
# on live/healthy system 
xxd -p < /bin/netcat | sed 's/../\\x&/g' | awk '{printf $0}' > netcat.dump
#                                     ^                 ^ strip newlines
#                                      \ convert 052348 to \x05\x23\x48

# copy the contents of netcat.dump into clipboard

# on the crippled system
builtin  echo -e "<PASTE>" > /netcat

# do magic to chmod netcat to +x
chmod +x /netcat

/netcat # should work!
``

**crucial trick**: `echo -e "foo" > /existing-file` will overwrite the existing file while maintaining its permissions.

### Step 1: build a thin chmod like so:

```c
#include <sys/stat.h>
#include <unistd.h>

int main(int argv, char** argc) {
    int result = chmod(argc[1], S_IRUSR | S_IWUSR | S_IXUSR);
}
```

build it without dependencies:

```bash
gcc mini-chmod.c -o mini-chmod -static
```

### Step 2: find a single file with the execute bit set on your file system

When I hit the equivalent of `rm -rf /`, I of course immediately hit CTRL+C+C+C+C+C within 250ms. But it was already too late.
But thankfully, this also left *some* files in my filesystem and I set about the slow and tedious process of finding any file that had its execute bit set.

So, build the `mini-chmod` binary, then encode it via

```bash 
    gcc mini-chmod.c -o mini-chmod -static # build the binary
    xxd -p < mini-chmod | sed 's/../\\x&/g' | awk '{printf $0}' > mini-chmod.dump # make it into a copy pasteable string
    
    # on broken system, paste (through the terminal) the following:
    echo -e "<ESCAPED BINARY>" > ./mini-chmod
```

## Step 3: proceed with the gameplan

The gameplan becomes that to:

1. get `nc` and `dd` on the disabled system
1. chmod them to be executable
1. `nc | dd of=/dev/mmcblk0p1` 
1. trigger a hard reboot

(note: see below for a minimal netcat implementation)

### `mini-netcat.c`

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define PORT 1234
#define BUFFER_SIZE 1024

int main(int argv, char** argc) {
    int sockfd, newsockfd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len;
    FILE *file;
    char buffer[BUFFER_SIZE];

    // Create a socket
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("Error opening socket");
        exit(1);
    }

    // Set up the server address
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // Bind the socket to the server address
    if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Error binding socket");
        exit(1);
    }

    // Listen for incoming connections
    listen(sockfd, 1);
    printf("Waiting for a connection on %d...\n", PORT);

    // Accept a client connection
    client_len = sizeof(client_addr);
    newsockfd = accept(sockfd, (struct sockaddr *)&client_addr, &client_len);
    if (newsockfd < 0) {
        perror("Error accepting connection");
        exit(1);
    }
    printf("Connected\n");

    // Open the file to write
    printf("%s", argc[1]);
    file = fopen(argc[1], "wb");
    if (file == NULL) {
        perror("Error opening file");
        exit(1);
    }

    // Receive and write the file data
    ssize_t bytes_read;
    while ((bytes_read = recv(newsockfd, buffer, BUFFER_SIZE, 0)) > 0) {
        fwrite(buffer, sizeof(char), bytes_read, file);
    }

    // Close the file and socket
    fclose(file);
    close(newsockfd);
    close(sockfd);

    printf("File received successfully.\n");

    return 0;
}
```

and for reference: ChatGPT was essentially utterly useless in this novel type of error. It only parroted the countless unhelpful stack overflow style comments by saying "why are you doing that?" and "maybe you should install <insert favorite distro>", and definitely sanctimonious shit like "you should leave that to the pros".
maybe I need to post all this to a substack for when humanity fades and there's one guy somewhere trying to rescue the last remaining 4 beaglebones.

final point.  this is the end game - the thanos snaps his fingers moment:

```bash
ssh root@10.1.2.3 "dd if=/dev/mmcblk0p1" | dd of=/dev/mmcblk0p1 status=progress
```

the thanos moment is followed by 

```bash
echo b > /proc/sysrq-trigger
```

because `reboot` won't be readable anymore.
