resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr_block # The IP address range for the VPC.
  instance_tenancy     = "default"          # Default tenancy for instances.
  enable_dns_support   = true               # Enable DNS resolution within the VPC.
  enable_dns_hostnames = true               # Enable DNS hostnames for instances.

  tags = {
    Name        = "${var.real_estate_api_project}-VPC-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}


resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.real_estate_api_project}-IGW-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}

# Resource: aws_subnet - Defines a public subnet.
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id        # Link to the VPC.
  cidr_block              = var.public_subnet_cidr # IP range for this subnet.
  availability_zone       = var.availability_zone  # Place in a specific AZ for fault tolerance.
  map_public_ip_on_launch = true                   # Automatically assign public IPs to instances launched here.

  tags = {
    Name        = "${var.real_estate_api_project}-PublicSubnet-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}

resource "aws_subnet" "private_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_cidr_2 # You'll need a new CIDR block variable for this, e.g., "10.0.3.0/24"
  availability_zone       = var.availability_zone_2
  map_public_ip_on_launch = false

  tags = {
    Name        = "${var.real_estate_api_project}-PrivateSubnet-2-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}


resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.4.0/24"  # New CIDR block for second public subnet
  availability_zone       = var.availability_zone_2
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.real_estate_api_project}-PublicSubnet-2-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}

# Associate the new public subnet with the public route table
resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# Create a new DB subnet group using PUBLIC subnets
resource "aws_db_subnet_group" "public_db" {
  name       = "${var.real_estate_api_project}-public-db-subnet-group-${var.environment}"
  subnet_ids = [aws_subnet.public.id, aws_subnet.public_2.id]

  tags = {
    Name        = "${var.real_estate_api_project}-Public-DBSG-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}



# Resource: aws_route_table - Defines the route table for the public subnet.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"                  # Destination: all internet traffic.
    gateway_id = aws_internet_gateway.main.id # Target: the Internet Gateway.
  }

  tags = {
    Name        = "${var.real_estate_api_project}-PublicRT-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}

# Resource: aws_route_table_association - Links the public subnet to its route table.
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Resource: aws_subnet - Defines a private subnet.
# Resources here do NOT have public IP addresses and are isolated from direct internet access.
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false # Do NOT automatically assign public IPs.

  tags = {
    Name        = "${var.real_estate_api_project}-PrivateSubnet-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}

# Resource: aws_route_table - Defines the route table for the private subnet.
# Initially, this route table has no internet egress.
# A NAT Gateway would be added here if private instances needed outbound internet access.
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.real_estate_api_project}-PrivateRT-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}

# Resource: aws_route_table_association - Links the private subnet to its route table.
resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

# Resource: aws_security_group - Defines a security group for public-facing resources (e.g., Web Server).
# This acts as a virtual firewall for resources associated with it.
resource "aws_security_group" "public_sg" {
  name        = "${var.real_estate_api_project}-PublicSG-${var.environment}"
  description = "Allow SSH, HTTP, and HTTPS access to public resources"
  vpc_id      = aws_vpc.main.id

  # Ingress (Inbound) Rules:
  # Allow SSH (Port 22) from anywhere (0.0.0.0/0).
  # WARNING: For production, we restrict this to your specific IP address.
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Be extremely cautious with this in production.
  }

  # Allow HTTP (Port 80) from anywhere.
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS (Port 443) from anywhere.
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress (Outbound) Rules:
  # Allow all outbound traffic.
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # -1 means all protocols.
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.real_estate_api_project}-PublicSG-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}

# Resource: aws_security_group - Defines a security group for private resources (e.g., Database).
# This SG allows traffic ONLY from the public_sg (web server) and all outbound traffic.
resource "aws_security_group" "private_sg" {
  name        = "${var.real_estate_api_project}-PrivateSG-${var.environment}"
  description = "Allow traffic from public SG to private resources, all outbound"
  vpc_id      = aws_vpc.main.id

  # Ingress (Inbound) Rules:
  # Allow all TCP traffic from the public_sg (your web server).
  # This ensures only your application can talk to your database.
  ingress {
    description     = "Allow all TCP from Public SG"
    from_port       = 0     # Or specific database port like 3306 for MySQL.
    to_port         = 65535 # Or specific database port like 3306 for MySQL.
    protocol        = "tcp"
    security_groups = [aws_security_group.public_sg.id] # Source is the ID of the public security group.
  }

  ingress {
    description = "PostgreSQL from my public IP"
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress (Outbound) Rules:
  # Allow all outbound traffic.
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # -1 means all protocols.
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.real_estate_api_project}-PrivateSG-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}


# outputs.tf: Defines output values that are useful to know after Terraform applies.
# These can be used by other Terraform configurations or for quick reference.
output "vpc_id" {
  description = "The ID of the created VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet."
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "The ID of the private subnet."
  value       = aws_subnet.private.id
}

output "public_security_group_id" {
  description = "The ID of the public security group."
  value       = aws_security_group.public_sg.id
}

output "private_security_group_id" {
  description = "The ID of the private security group."
  value       = aws_security_group.private_sg.id
}

output "db_instance_address" {
  description = "The DNS address of the PostgreSQL DB instance."
  value       = aws_db_instance.postgresql_db.address
}

output "db_instance_port" {
  description = "The port of the PostgreSQL DB instance."
  value       = aws_db_instance.postgresql_db.port
}

output "db_instance_username" {
  description = "The master username for the PostgreSQL DB instance."
  value       = aws_db_instance.postgresql_db.username
}

output "db_instance_name" {
  description = "The name of the initial database created."
  value       = aws_db_instance.postgresql_db.db_name
}
