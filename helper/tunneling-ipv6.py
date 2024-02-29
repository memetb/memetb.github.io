from diagrams import Cluster, Diagram, Edge

from diagrams.digitalocean.compute import Droplet
from diagrams.onprem.client import Users
from diagrams.generic.compute import Rack
from diagrams.saas.cdn import Cloudflare
from diagrams.gcp.analytics import BigQuery, Dataflow, PubSub
from diagrams.gcp.compute import AppEngine, Functions
from diagrams.gcp.database import BigTable
from diagrams.gcp.iot import IotCore
from diagrams.gcp.storage import GCS
from diagrams.generic.os import Debian
from diagrams.onprem.security import Vault
from diagrams.onprem.container import Docker
from diagrams.onprem.network import Nginx, Internet
from diagrams.onprem.vcs import Gitea
from diagrams.onprem.ci import Concourseci
from diagrams.custom import Custom
from urllib.request import urlretrieve

from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.database import ElastiCache, RDS
from diagrams.aws.network import ELB
from diagrams.aws.network import Route53


vm = {"bgcolor": "#ffeae8"}
container = {"bgcolor": "#fcfcff"}

#keycloak_icon_url = "https://upload.wikimedia.org/wikipedia/commons/2/29/Keycloak_Logo.png"
#keycloak_icon = "../enterprise/assets/keycloak.png"
#urlretrieve(keycloak_icon_url, keycloak_icon)

with Diagram(show=False, direction="TB", filename="assets/tunneling-ipv6"):
	#dns = Route53("dns")

	with Cluster("Home network"):
		group = [r1 := Rack("Your server #1"),
				 r2 := Rack("Your server #2")]

	droplet = Droplet("bastion")
	Users() >> Edge(label="   ipv4") >> Cloudflare("Proxy") >> droplet >> Edge(label="ipv6") >> group
