terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "function_name" {
  type    = string
  default = "solace-event-portal-mcp"
}

variable "solace_api_token" {
  type      = string
  sensitive = true
}

variable "solace_api_base_url" {
  type    = string
  default = "https://api.solace.cloud"
}

variable "python_version" {
  type    = string
  default = "python3.12"
}

resource "null_resource" "build_lambda_package" {
  triggers = {
    requirements = filemd5("${path.module}/../solace-event-portal-designer-mcp/requirements.txt")
    source_code  = sha256(join("", [for f in fileset("${path.module}/../solace-event-portal-designer-mcp/src", "**/*.py") : filesha256("${path.module}/../solace-event-portal-designer-mcp/src/${f}")]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      rm -rf ${path.module}/package
      mkdir -p ${path.module}/package

      pip3 install \
        --target ${path.module}/package \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.12 \
        --only-binary=:all: \
        --upgrade \
        -r ${path.module}/../solace-event-portal-designer-mcp/requirements.txt

      pip3 install \
        --target ${path.module}/package \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.12 \
        --only-binary=:all: \
        --upgrade \
        mangum

      cp -r ${path.module}/../solace-event-portal-designer-mcp/src/* ${path.module}/package/
      cp ${path.module}/lambda_handler.py ${path.module}/package/

      if [ -d "${path.module}/../solace-event-portal-designer-mcp/src/solace_event_portal_designer_mcp/data" ]; then
        mkdir -p ${path.module}/package/solace_event_portal_designer_mcp/data
        cp -r ${path.module}/../solace-event-portal-designer-mcp/src/solace_event_portal_designer_mcp/data/* \
              ${path.module}/package/solace_event_portal_designer_mcp/data/
      fi

      find ${path.module}/package -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
      find ${path.module}/package -type f -name "*.pyc" -delete 2>/dev/null || true
    EOT
  }
}

data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/package"
  output_path = "${path.module}/lambda_function.zip"

  depends_on = [null_resource.build_lambda_package]
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 7
}

resource "aws_lambda_function" "mcp_server" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = var.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_handler.handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = var.python_version
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      SOLACE_API_TOKEN    = var.solace_api_token
      SOLACE_API_BASE_URL = var.solace_api_base_url
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
    aws_iam_role_policy_attachment.lambda_basic
  ]
}

resource "aws_lambda_function_url" "mcp_server_url" {
  function_name      = aws_lambda_function.mcp_server.function_name
  authorization_type = "NONE"
}

output "lambda_function_name" {
  value = aws_lambda_function.mcp_server.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.mcp_server.arn
}

output "lambda_function_url" {
  value = aws_lambda_function_url.mcp_server_url.function_url
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}
