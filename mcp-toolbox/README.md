# MCP Toolbox for Databases - Quick Start Guide

## 📋 Overview

The MCP Toolbox for Databases is an open-source MCP server that enables AI agents to interact with databases. This directory contains the toolbox binary and configuration files for connecting to AlloyDB and other databases.

## 🚀 Quick Start

### 1. Set Up Environment Variables

Create a `.env` file in this directory with your database credentials:

```bash
# Google Cloud Project
export GCP_PROJECT_ID="your-project-id"

# AlloyDB Production
export ALLOYDB_USER="your-user@your-domain.com"
export ALLOYDB_PASSWORD="your-password"  # Leave empty for IAM auth

# AlloyDB Development
export DEV_USER="dev-user"
export DEV_PASSWORD="dev-password"

# Local PostgreSQL
export LOCAL_USER="postgres"
export LOCAL_PASSWORD="postgres"
```

Load the environment variables:
```bash
source .env
```

### 2. Create Your Configuration File

Copy the example configuration and customize it:

```bash
cp tools.yaml.example tools.yaml
# Edit tools.yaml with your actual database details
```

### 3. Run the Toolbox

#### Option A: Using Prebuilt Configuration (Easiest)

For quick testing with AlloyDB:

```bash
./toolbox --prebuilt alloydb-postgres
```

Available prebuilt configurations:
- `alloydb-postgres` - Standard AlloyDB PostgreSQL tools
- `alloydb-postgres-admin` - Admin-focused tools
- `alloydb-postgres-observability` - Observability tools
- `postgres` - Generic PostgreSQL
- `bigquery` - BigQuery analytics
- And many more (see `./toolbox --help`)

#### Option B: Using Custom Configuration

With your custom `tools.yaml`:

```bash
./toolbox --tools-file tools.yaml
```

#### Option C: MCP STDIO Mode (for AI assistants)

For integration with AI assistants that support MCP:

```bash
./toolbox --tools-file tools.yaml --stdio
```

#### Option D: With UI (Web Interface)

Launch the web UI for interactive testing:

```bash
./toolbox --tools-file tools.yaml --ui
```

Then open http://127.0.0.1:5000 in your browser.

### 4. Advanced Options

#### Custom Port and Address

```bash
./toolbox --tools-file tools.yaml --port 8080 --address 0.0.0.0
```

#### Enable Logging

```bash
./toolbox --tools-file tools.yaml --log-level DEBUG
```

#### Multiple Configuration Files

```bash
./toolbox --tools-files config1.yaml,config2.yaml,config3.yaml
```

#### Load All YAML Files from a Directory

```bash
./toolbox --tools-folder ./configs/
```

## 🔐 Authentication

### AlloyDB Authentication Methods

#### 1. Password Authentication (Standard)

```yaml
sources:
  my-alloydb:
    kind: alloydb-postgres
    project: my-project
    region: us-central1
    cluster: my-cluster
    instance: my-instance
    database: my_db
    user: myuser
    password: ${PASSWORD}
```

#### 2. IAM Authentication (Recommended)

**Option A: Specify IAM email**
```yaml
sources:
  my-alloydb:
    kind: alloydb-postgres
    project: my-project
    region: us-central1
    cluster: my-cluster
    instance: my-instance
    database: my_db
    user: your-email@your-domain.com
    # password field is omitted
```

**Option B: Use Application Default Credentials**
```yaml
sources:
  my-alloydb:
    kind: alloydb-postgres
    project: my-project
    region: us-central1
    cluster: my-cluster
    instance: my-instance
    database: my_db
    # Both user and password fields are omitted
```

### Setting Up Application Default Credentials (ADC)

```bash
# Authenticate with your Google Cloud account
gcloud auth application-default login

# Or use a service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Required IAM Permissions

Your IAM identity needs these roles:
- `roles/alloydb.client`
- `roles/serviceusage.serviceUsageConsumer`

Grant them with:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:your-email@your-domain.com" \
  --role="roles/alloydb.client"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:your-email@your-domain.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

## 🌐 Networking

### Public IP vs Private IP

AlloyDB supports both connection types:

**Public IP** (internet-accessible):
```yaml
ipType: "public"
```

**Private IP** (VPC-only):
```yaml
ipType: "private"
```

For more information, see:
- [Public IP Connection](https://cloud.google.com/alloydb/docs/connect-public-ip)
- [Private IP Connection](https://cloud.google.com/alloydb/docs/private-ip)
- [Connection Overview](https://cloud.google.com/alloydb/docs/connection-overview)

## 📝 Configuration Structure

### Sources

Define your database connections:

```yaml
sources:
  source-name:
    kind: alloydb-postgres  # or postgres, bigquery, mysql, etc.
    # Connection parameters...
```

### Tools

Define actions AI agents can perform:

```yaml
tools:
  tool-name:
    kind: postgres-sql
    source: source-name
    description: What this tool does
    parameters:
      - name: param1
        type: string
        description: Parameter description
    statement: |
      SELECT * FROM table WHERE column = $1;
```

### Toolsets

Group tools for different use cases:

```yaml
toolsets:
  my-toolset:
    - tool1
    - tool2
    - tool3
```

### Prompts

Define reusable LLM prompts:

```yaml
prompts:
  prompt-name:
    description: What this prompt does
    messages:
      - content: "Your prompt with {{.variable}}"
    arguments:
      - name: variable
        description: Variable description
```

## 🧪 Testing Your Setup

### 1. Test the Binary

```bash
./toolbox --version
```

### 2. Validate Configuration

```bash
./toolbox --tools-file tools.yaml --log-level DEBUG
```

Check the logs for any configuration errors.

### 3. Test with UI

```bash
./toolbox --tools-file tools.yaml --ui
```

Open http://127.0.0.1:5000 and test your tools interactively.

## 🔧 Troubleshooting

### Connection Issues

1. **Check IAM permissions**: Ensure your account has the required roles
2. **Verify network access**: Confirm your IP type matches your cluster configuration
3. **Test credentials**: Try connecting with `psql` or another PostgreSQL client first
4. **Check ADC**: Run `gcloud auth application-default print-access-token` to verify

### Configuration Errors

1. **Validate YAML syntax**: Use a YAML validator
2. **Check environment variables**: Ensure all `${VAR}` references are set
3. **Review logs**: Run with `--log-level DEBUG` for detailed error messages

### Common Errors

**"connection refused"**
- Check if the instance is running
- Verify network connectivity
- Ensure correct `ipType` setting

**"authentication failed"**
- Verify credentials
- Check IAM permissions for IAM auth
- Ensure database user exists

**"database does not exist"**
- Verify database name
- Check if you have access to the database

## 📚 Additional Resources

- **Official Documentation**: https://googleapis.github.io/genai-toolbox/
- **GitHub Repository**: https://github.com/googleapis/genai-toolbox
- **AlloyDB Documentation**: https://cloud.google.com/alloydb/docs
- **MCP Protocol**: https://modelcontextprotocol.io/

## 🔄 Updating the Toolbox

Check for new versions:
```bash
# Visit the releases page
open https://github.com/googleapis/genai-toolbox/releases

# Download the latest version (example for v0.25.0)
export VERSION=0.25.0
curl -L -o toolbox-new https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/arm64/toolbox
chmod +x toolbox-new
mv toolbox-new toolbox
```

Or use Homebrew:
```bash
brew upgrade mcp-toolbox
```

## 💡 Tips

1. **Use environment variables** for sensitive data instead of hardcoding
2. **Start with prebuilt configurations** to test connectivity
3. **Use the UI** for interactive development and testing
4. **Enable debug logging** when troubleshooting
5. **Group related tools** into toolsets for better organization
6. **Document your tools** with clear descriptions for AI agents

## 🤝 Integration with AI Assistants

### Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "alloydb": {
      "command": "/path/to/devbridge/mcp-toolbox/toolbox",
      "args": ["--tools-file", "/path/to/devbridge/mcp-toolbox/tools.yaml", "--stdio"]
    }
  }
}
```

### Gemini CLI Extensions

```bash
gemini extensions install https://github.com/gemini-cli-extensions/mcp-toolbox
```

## 📧 Support

For issues and questions:
- GitHub Issues: https://github.com/googleapis/genai-toolbox/issues
- Stack Overflow: Tag with `alloydb` and `mcp-toolbox`
