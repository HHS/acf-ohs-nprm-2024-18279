# OHS NPRM Cloud Architecture

According to ACF OHS’s request, data files and code files should reside on the AWS infrastructure - virtual machine (vm): a EC2 instance - ohs-vm-aws, where a VPN gateway is created to link this AWS vm to the Azure virtual machine (ohs-vm) to secure the comment prompts passing and OpenAI Generative Pre-trained Transformers (GPT) models’ response data transfer. The OpenAI GPT models are only hosted on Azure OpenAI endpoints. For the data security purpose, those endpoints are associated with Arch subscription (RS-OHS-RCI-01-SUB) and are kept privately only to link to the Azure virtual machine in a virtual subnet (OHS-Vnet), where the AWS virtual machine can access OpenAI endpoints GPT models to perform thematic grouping analysis. Below is a detailed outline of the resources that were set up in AWS and Azure in order to host the pipeline for this project.

![image](https://github.com/HHS/acf-ohs-nprm-2023/assets/150829968/dfdbaa4a-c391-4da2-90c5-c3c4a66bf4ce)

## Resources set up in AWS
In AWS, a VPC is created to host virtual machine instance, where the data file and python code resided. A Subnet and internet gateway is created to allow user to upload data onto virtual machine (ohs-vm-aws). Route tables, VPN, Network ACLs and Security Groups are securely constructed to connect AWS virtual machine with Azure virtual machine together, that allows the comment prompt to be passed through the VPN gateway to the OpenAI GPT model hosted in Azure virtual subnet and gets the GPT thematic analysis and summary results back to AWS virtual machine.

**Virtual Private Cloud**
- Name: ohs-vpc
- ID: vpc-0fdf78531320b36fa 
- Region: US East - ohio
*Note: VPC is where Virtual Machine was hosted*

**Subnet Configuration:**
- Public Subnets:
  * Subnet 1: 
    - Name: ohs-subnet-public1-us-east-2a
    - ID: subnet-05655b430b97ee0c5
    - CIDR: 172.20.0.0/20
  * Subnet 2:
    - Name: ohs-subnet-public2-us-east-2b
    - ID: subnet-0e7dd13884e1accbc
    - CIDR: 172.20.16.0/20
- Private Subnets:
  * Subnet 3:
    - Name: ohs-subnet-private1-us-east-2a
    - ID: subnet-00e91be44994bfb5a
    - CIDR: 172.20.128.0/20
  * Subnet 4:
    - Name: ohs-subnet-private2-us-east-2b
    - ID: subnet-02e064812ae7ef59c
    - CIDR: 172.20.144.0/20

**Internet Gateway**
- Name: ohs-igw
- ID: igw-031b730be6496df61

*Note: An Internet Gateway is attached to enable communication between the VPC and the Internet.*

**Route Table**
- Public Route Table:
  * Name: ohs-rtb-public
  * ID: rtb-05e7b5f4f834b735f
- Private Route Table:
  * Table 1:
    - Name: ohs-rtb-private1-us-east-2a
    - ID: rtb-017ad9355468af2d0
  * Table 2:
    - Name: ohs-rtb-private2-us-east-2b
    - ID: rtb-0a8b034b90715a929

*Note: Public route table associates public subnets with the Internet Gateway and routes traffic to the Internet; Private route table does not have an Internet Gateway association, but routes traffic internally and to the Azure network.*

**Network ACLs:**
- Name: ohs-nacl
- ID: acl-0d9d96eeef25c7520
*Note: Inbound and Outbound Rules to the Network.*
**SSH Security Group:**
- Name: ohs-vpc-sg-2
- ID: sg-0a4656fcd32a5bf9c
*Note: SSH Security Group permits SSH connection from Azure network.*
**VPN Connection:**
- VPN Gateway:
  * Name: ohs-azure-gw
  * ID: vgw-02857925d9c016f46
- Customer Gateway:
  * Gateway 1:
    - Name: ohs-ToAzureInstance1
    - ID: cgw-0d22404e4669c5c73
  * Gateway 2:
    - Name: ohs-ToAzureInstance0
    - ID: cgw-01d0a5a5c833c5c9d
- Site-to-Site VPN Connection:
  * VPN 1:
    - Name: ohs-ToAzureInstance1-vpn
    - ID: vpn-0d2beead3a9cab5b7
  * VPN 2:
    - Name: ohs-ToAzureInstance0-vpn
    - ID: vpn-022d6809634472c57
*Note: VPN connection is created to have private connection between AWS virtual machine and Azure virtual machine.*

**Virtual Machine:** 
- Name: ohs-vm-aws
- ID: i-0113cf2b9b8c31b48
- Instance Type: t2.xlarge
- AMI (Amazon Machine Image): ami-0ee4f2271a4df2d7d
- Key Pair: ohs-vm-aws
- Security Group ID: sg-0a4656fcd32a5bf9c
- Storage Configuration:
  * Volume Name: ohsvm-volume
  * ID: vol-07dc21957608d11a4
  * Size: 60 GB
  * Volume Type: gp3
- Network Information:
  * VPC ID: vpc-0fdf78531320b36fa
  * Subnet ID: subnet-0e7dd13884e1accbc
  * Public IP Address: 3.135.240.113
  * Private IP Address: 172.20.25.77
  * Network Interface ID: eni-065824364cbfc11c0
*Note: Virtual Machine instance is created to host data file and python code to perform thematic analysis.*

## Resources set up in Azure
One Azure OpenAI Instance (ohs2-Language-Ingest) with one model (Language-Ingest) and its private endpoint (https://ohsp2-language-ingest.openai.azure.com) has been created to handle foreign language comments translating into English, and two Azure OpenAI Instances (ohs-gpt4-1106-preview and ohs-gpt4-1106-preview-1) with 9 GPT4 models and their private endpoints (https://ohs-gpt4-1106-preview.openai.azure.com and https://ohs-gpt4-1106-preview-1.openai.azure.com) have been created to parallelly perform thematic grouping and summary analysis. 
**Virtual Machine:** 
- Name: ohs-vm
- Bastion Host: OHS-Vnet-bastion
*Note: A virtual machine is created to be associated with virtual network and connect to the Azure OpenAI instance through their private endpoints with private IP addresses. Azure Bastion acts as a jump server, enabling secure access to virtual machines in Azure without exposing them to the public internet.*
**Virtual Network:** 
- Name: OHS-Vnet [10.0.0.0/16]
- Location: East US 2
- Subnet Configuration:
  * GatewaySubnet: [10.0.2.0/27]
  * OHS-Subnet-1: [10.0.0.0/24]
  * OHS-Subnet-2: [10.0.3.0/24]
  * AzureBastionSubnet: [10.0.1.0/26]

*Note: A virtual network is an isolated network environment in Azure and it is created to link the Azure OpenAI instance with Azure virtual machine where the AWS virtual machine has connections with. It spans the IP address range of 10.0.0.0/16 and comprises several subnets for organizing resources logically. Three subnets are defined: Gateway Subnet (for VPN gateway), OHS-Subnet-1, and OHS-Subnet-2. Additionally, there is AzureBstionSubnet designated for Azure Bastion service, enhancing security for remote access.*

**Network Security Groups (NSG):** 
- Name: ohs-vnet-nsg
*Note: Network Security Groups is created to securely connect AWS virtual machine with Azure virtual machine. It controls inbound and outbound traffic to and from Azure resources within the virtual network, enhancing security policies.*
**Route Tables:** 
- Name: ohs-azure-aws-route
  
| Name | Address Prefix | Next Hop Type | Next Hop IP Address| 
| --- | --- | --- | --- |
| azure_aws_route | 172.20.0.0/16 | Virtual Network Gateway | - |

*Note: Route table is created to define routes for directing traffic between Azure and AWS networks. Specifically, it ensures that traffic destined for the AWS network (172.20.0.0/16) is routed through the VPN gateway.*

**Azure OpenAI Instances and model deployed:**
- Name: ohsp2-Language-Ingest:
  * Model: Language-Ingest
- Name: ohs-gpt4-1106-preview:
  * Model: ohs-gpt4-1106-preview
  * Model: ohs-gpt4-1106-1
  * Model: ohs-gpt4-1106-2
  * Model: ohs-gpt4-1106-3
  * Model: ohs-gpt4-1106-4 
- Name: ohs-gpt4-1106-preview-1:
  * Model: ohs-gpt4-1106-preview
  * Model: ohs-gpt4-1106-preview-1
  * Model: ohs-gpt4-1106-preview-2
  * Model: ohs-gpt4-1106-preview-3 
*Note: Azure OpenAI instances with models are created to allow AWS virtual machine to call GPT model for thematic analysis.*

**OpenAI private endpoints:**
- Name: openai-language:
  * URL: https://ohsp2-language-ingest.openai.azure.com
- Name: ohs-gpt4-1106-preview:
  * URL: https://ohs-gpt4-1106-preview.openai.azure.com
- Name: ohs-gpt4-1106-preview-1:
  * URL: https://ohs-gpt4-1106-preview-1.openai.azure.com
*Note: OpenAI private endpoints are created to limit the Azure OpenAI instance only being called with the Azure virtual network, no public traffic is allowed for those OpenAI models.*

**Network Interface:**
- Name: openai-language-nic
- Name: ohs-gpt4-1106-preview-nic
- Name: ohs-gpt4-1106-preview-1-nic
*Note: Network Interface is created for private endpoints of those Azure OpenAI endpoints. It will allow AWS virtual machine to connect to Azure OpenAI GPT models.*

**VPN Gateway:** 
- Name: ohs-vnet-GW
*Note: VPN Gateway connects AWS virtual machine to Azure virtual machine. It serves as the Azure-side endpoint for VPN connections to AWS. It establishes secure communication channels between Azure and AWS networks, enabling data exchange over encrypted tunnels.*
**Local Network Gateway and VPN Connections:**
- Name: ohs-AWSTunnel1ToInstance0:
  * ohs-AWSTunnel1toAzureInstance0-vpn
- Name: ohs-AWSTunnel1toInstance1:
  * ohs-AWSTunnel1toAzureInstance1-vpn
- Name: ohs-AWSTunnel2ToInstance0:
  * ohs-AWSTunnel2toAzureInstance0-vpn
- Name: ohs-AWSTunnel2ToInstance1:
  * ohs-AWSTunnel2toAzureInstance1-vpn
*Note: VPN gateway and connections are created to have private connection between AWS and Azure networks. They consist of multiple VPN connections, each associated with specific AWS instances. Each VPN connection establishes a secure tunnel for data transmission between Azure and AWS instances, ensuring confidentiality and integrity.*

**Dashboard:** 
- Name: OHS-PROJECT-DASHBOARD
*Note: Dashboard is created to provide a centralized interface for monitoring the health, performance, and usage of the private OpenAI endpoints, virtual machine, Network and other resources.*

**Log Analytics Workspace:**
- Name: ohs-vm-loganalytics
- Name: ohs-openai-endpoints-loganalytics
- Name: ohs-network-lognalaytics
  
*Note: Log Analytics Workspaces are created to further understand the virtual machine and Azure OpenAI endpoints usage and network connections behaviors. They are centralized repositories and platforms for collecting, analyzing, and visualizing log data. They aggregate data from the virtual machine, network, and OpenAI private endpoints, and Redis.*

**Storage Accounts:**
- Name: ohslogstorage
- Name: ohsrcistorage
  
*Note: Storage Accounts are created to save those log files.*

**KeyVault:**
- Name: ohsrci-keyvault
 
*Note: KeyVault is created to provide a centralized location for managing cryptographic keys, secrets, and certificates. It stores the Azure and AWS virtual machine security keys.*


