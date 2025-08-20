resource "aws_db_subnet_group" "main" {
  name = "${var.real_estate_api_project}-db-subnet-group-${var.environment}"
  subnet_ids = [aws_subnet.private.id, aws_subnet.private_2.id]
  tags = {
      Name        = "${var.real_estate_api_project}-DBSG-${var.environment}"
      Project     = var.real_estate_api_project
      Environment = var.environment
  }
}
resource "aws_db_instance" "postgresql_db" {
  identifier = "${replace(lower(var.real_estate_api_project), "_", "-")}-postgresql-db-${lower(var.environment)}"
   # Database engine configuration
  engine         = "postgres"        # Specify PostgreSQL.
  engine_version = "14.18"            # Choose a stable and supported version.

  # Instance sizing and storage
  instance_class    = "db.t3.micro" # Use a free-tier eligible instance type for learning.
  allocated_storage = 20            # Allocated storage in GB (minimum for free tier is 20 GB).
  storage_type      = "gp2"         # General Purpose SSD.

  # Database credentials and name
  db_name  = "${var.real_estate_api_project}_db" # The initial database name to be created.
  username = "lewis"                 # Master username for the database.
  password = var.db_password

  db_subnet_group_name = aws_db_subnet_group.public_db.name # Link to the DB Subnet Group.
  # Link to the security group that allows access to this database.
  vpc_security_group_ids = [aws_security_group.private_sg.id]
  publicly_accessible    = true # IMPORTANT: Set to false for production to keep it private.

  # Backup and maintenance
  backup_retention_period = 7 # Retain backups for 7 days.
  skip_final_snapshot     = true # Set to true for development to speed up deletion.
                                 # For production, set to false to require a final snapshot before deletion.

  # Tags for organization and cost tracking
  tags = {
    Name        = "${var.real_estate_api_project}-PostgreSQL-${var.environment}"
    Project     = var.real_estate_api_project
    Environment = var.environment
  }
}