# MCP Toolbox Quick Reference

## 🚀 Quick Commands

### Start the Server

```bash
# With custom configuration
./toolbox --tools-file tools.yaml

# With prebuilt AlloyDB config
./toolbox --prebuilt alloydb-postgres

# With UI (web interface)
./toolbox --tools-file tools.yaml --ui

# MCP STDIO mode (for AI assistants)
./toolbox --tools-file tools.yaml --stdio
```

### Setup Script

```bash
# Run interactive setup
./setup.sh

# Quick options:
# 1 - Check requirements
# 2 - Create .env template
# 3 - Create minimal config
# 4 - Test configuration
# 5 - Run with UI
# 6 - Run with prebuilt config
```

## 📝 Configuration Snippets

### AlloyDB Source (IAM Auth)

```yaml
sources:
  my-alloydb:
    kind: alloydb-postgres
    project: my-project-id
    region: us-central1
    cluster: my-cluster
    instance: my-instance
    database: my_db
    user: user@domain.com
    # password omitted for IAM auth
    ipType: "private"
```

### AlloyDB Source (Password Auth)

```yaml
sources:
  my-alloydb:
    kind: alloydb-postgres
    project: my-project-id
    region: us-central1
    cluster: my-cluster
    instance: my-instance
    database: my_db
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    ipType: "public"
```

### Simple SQL Tool

```yaml
tools:
  find-user:
    kind: postgres-sql
    source: my-alloydb
    description: Find user by email
    parameters:
      - name: email
        type: string
        description: User email address
    statement: |
      SELECT * FROM users WHERE email = $1;
```

### BigQuery Source

```yaml
sources:
  my-bigquery:
    kind: bigquery
    project: my-project-id
    dataset: my_dataset
```

### Local PostgreSQL

```yaml
sources:
  local-db:
    kind: postgres
    host: 127.0.0.1
    port: 5432
    database: mydb
    user: postgres
    password: ${PG_PASSWORD}
```

## 🔐 Authentication Setup

### Google Cloud ADC

```bash
# Login with your account
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Grant IAM Permissions

```bash
# For AlloyDB access
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:EMAIL" \
  --role="roles/alloydb.client"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:EMAIL" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

## 🧪 Testing

### Test Connection

```bash
# Start with debug logging
./toolbox --tools-file tools.yaml --log-level DEBUG

# Test with UI
./toolbox --tools-file tools.yaml --ui
# Then open http://127.0.0.1:5000
```

### Validate Configuration

```bash
# Check syntax
yamllint tools.yaml

# Test loading
./toolbox --tools-file tools.yaml --log-level INFO
```

## 🔧 Common Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--tools-file` | Single config file | `--tools-file tools.yaml` |
| `--tools-files` | Multiple config files | `--tools-files a.yaml,b.yaml` |
| `--tools-folder` | Directory of configs | `--tools-folder ./configs/` |
| `--prebuilt` | Use prebuilt config | `--prebuilt alloydb-postgres` |
| `--stdio` | MCP STDIO mode | `--stdio` |
| `--ui` | Launch web UI | `--ui` |
| `--port` | Server port | `--port 8080` |
| `--address` | Server address | `--address 0.0.0.0` |
| `--log-level` | Logging level | `--log-level DEBUG` |
| `--version` | Show version | `--version` |

## 📦 Prebuilt Configurations

### AlloyDB
- `alloydb-postgres` - Standard tools
- `alloydb-postgres-admin` - Admin tools
- `alloydb-postgres-observability` - Monitoring tools

### Cloud SQL
- `cloud-sql-postgres`
- `cloud-sql-mysql`
- `cloud-sql-mssql`
- `cloud-sql-postgres-admin`
- `cloud-sql-mysql-admin`
- `cloud-sql-mssql-admin`

### Other Databases
- `postgres` - Generic PostgreSQL
- `mysql` - Generic MySQL
- `bigquery` - BigQuery analytics
- `spanner` - Cloud Spanner
- `firestore` - Firestore
- `mongodb` - MongoDB
- `neo4j` - Neo4j graph database
- `elasticsearch` - Elasticsearch

## 🐛 Troubleshooting

### Check Version
```bash
./toolbox --version
```

### Test Binary
```bash
./toolbox --help
```

### Verify ADC
```bash
gcloud auth application-default print-access-token
```

### Check Environment Variables
```bash
source .env
echo $GCP_PROJECT_ID
```

### Common Issues

**"connection refused"**
- Check instance is running
- Verify network access
- Confirm ipType setting

**"authentication failed"**
- Verify credentials
- Check IAM permissions
- Ensure user exists in database

**"permission denied"**
- Grant required IAM roles
- Check service account permissions

## 📚 Resources

- **Docs**: https://googleapis.github.io/genai-toolbox/
- **GitHub**: https://github.com/googleapis/genai-toolbox
- **AlloyDB**: https://cloud.google.com/alloydb/docs
- **MCP Protocol**: https://modelcontextprotocol.io/

## 💡 Pro Tips

1. Use environment variables for secrets: `${VAR_NAME}`
2. Start with prebuilt configs for testing
3. Use `--ui` flag for interactive development
4. Enable debug logging when troubleshooting
5. Group related tools into toolsets
6. Test locally before deploying to production
7. Use IAM authentication in production
8. Keep configuration files in version control (without secrets)

## 🔄 Update Toolbox

```bash
# Check latest version
open https://github.com/googleapis/genai-toolbox/releases

# Download new version
export VERSION=0.25.0
curl -L -o toolbox https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/arm64/toolbox
chmod +x toolbox

# Or use Homebrew
brew upgrade mcp-toolbox
```
