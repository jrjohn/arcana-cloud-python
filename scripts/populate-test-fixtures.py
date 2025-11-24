#!/usr/bin/env python3
"""
Populate Test Fixtures in Kubernetes Database

This script populates the Kubernetes MySQL database with test fixture users
that are expected by the pytest test suite. It creates users with properly
hashed passwords compatible with the Werkzeug password hashing used by the
User model.

Usage:
    python3 scripts/populate-test-fixtures.py [--namespace NAMESPACE]
"""
import argparse
import subprocess
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash


# Test fixture users configuration
FIXTURE_USERS = [
    {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123',
        'role': 'user',
        'first_name': 'Test',
        'last_name': 'User',
        'is_verified': True,
        'is_active': True,
        'status': 'active'
    },
    {
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'AdminPass123',
        'role': 'admin',
        'first_name': 'Admin',
        'last_name': 'User',
        'is_verified': True,
        'is_active': True,
        'status': 'active'
    }
]


def generate_password_hashes():
    """Generate password hashes for all fixture users."""
    for user in FIXTURE_USERS:
        user['password_hash'] = generate_password_hash(user['password'])
    return FIXTURE_USERS


def escape_sql_string(value):
    """Escape single quotes in SQL strings."""
    if value is None:
        return 'NULL'
    return f"'{str(value).replace(chr(39), chr(39) + chr(39))}'"


def generate_insert_sql(users):
    """Generate SQL INSERT statements for fixture users."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    sql_statements = []

    for user in users:
        # Convert boolean to int (MySQL TINYINT)
        is_verified = 1 if user['is_verified'] else 0
        is_active = 1 if user['is_active'] else 0

        sql = f"""INSERT INTO users (
    username,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    status,
    is_verified,
    is_active,
    created_at,
    updated_at
) VALUES (
    {escape_sql_string(user['username'])},
    {escape_sql_string(user['email'])},
    {escape_sql_string(user['password_hash'])},
    {escape_sql_string(user['first_name'])},
    {escape_sql_string(user['last_name'])},
    {escape_sql_string(user['role'])},
    {escape_sql_string(user['status'])},
    {is_verified},
    {is_active},
    '{timestamp}',
    '{timestamp}'
);"""

        sql_statements.append(sql)

    return '\n'.join(sql_statements)


def execute_sql_in_k8s(sql, namespace='arcana-cloud', database='arcana_cloud'):
    """
    Execute SQL commands in the Kubernetes MySQL pod.

    Args:
        sql: SQL command to execute
        namespace: Kubernetes namespace
        database: Database name

    Returns:
        True if successful, False otherwise
    """
    # MySQL connection parameters
    mysql_user = 'arcana'
    mysql_password = 'arcana_pass'

    # Build the kubectl exec command
    kubectl_cmd = [
        'kubectl', 'exec', '-n', namespace,
        'mysql-0', '--',
        'mysql',
        '-u', mysql_user,
        f'-p{mysql_password}',
        database,
        '-e', sql
    ]

    try:
        # Execute the command
        result = subprocess.run(
            kubectl_cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # Filter out password warning from output
        if result.stderr and 'Warning: Using a password' not in result.stderr:
            print(f"MySQL stderr: {result.stderr}", file=sys.stderr)

        if result.stdout:
            print(result.stdout)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error executing SQL: {e}", file=sys.stderr)
        if e.stdout:
            print(f"stdout: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        return False


def check_k8s_mysql_pod(namespace='arcana-cloud'):
    """Check if the MySQL pod is running in Kubernetes."""
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'pod', '-n', namespace, 'mysql-0'],
            capture_output=True,
            text=True,
            check=True
        )
        return 'Running' in result.stdout
    except subprocess.CalledProcessError:
        return False


def populate_fixtures(namespace='arcana-cloud', verbose=False):
    """
    Main function to populate test fixtures.

    Args:
        namespace: Kubernetes namespace
        verbose: Print verbose output

    Returns:
        True if successful, False otherwise
    """
    print(f"Populating test fixtures in namespace: {namespace}")

    # Check if MySQL pod exists
    if not check_k8s_mysql_pod(namespace):
        print(f"Error: MySQL pod 'mysql-0' not found in namespace '{namespace}'", file=sys.stderr)
        return False

    print("✓ MySQL pod found")

    # Generate password hashes
    print("Generating password hashes...")
    users = generate_password_hashes()

    if verbose:
        print("\nFixture users:")
        for user in users:
            print(f"  - {user['username']} ({user['email']}) - role: {user['role']}")

    # Generate SQL
    print("Generating SQL statements...")
    sql = generate_insert_sql(users)

    if verbose:
        print("\nSQL to execute:")
        print(sql)
        print()

    # Delete existing fixture users first (to handle re-runs)
    print("Removing existing fixture users if any...")
    # Need to disable foreign key checks and delete oauth_tokens first
    # Delete by both username AND email to handle various states
    delete_sql = """
    SET FOREIGN_KEY_CHECKS=0;
    DELETE FROM oauth_tokens WHERE user_id IN (
        SELECT id FROM users WHERE username IN ('testuser', 'admin', 'test')
        OR email IN ('test@example.com', 'admin@example.com')
    );
    DELETE FROM users WHERE username IN ('testuser', 'admin', 'test')
        OR email IN ('test@example.com', 'admin@example.com');
    SET FOREIGN_KEY_CHECKS=1;
    """

    if not execute_sql_in_k8s(delete_sql, namespace):
        print("Warning: Failed to delete existing fixture users (may not exist)", file=sys.stderr)

    print("✓ Cleaned up existing fixtures")

    # Insert fixture users
    print("Inserting fixture users...")
    if not execute_sql_in_k8s(sql, namespace):
        print("Error: Failed to insert fixture users", file=sys.stderr)
        return False

    print("✓ Fixture users inserted")

    # Verify insertion
    verify_sql = "SELECT username, email, role, status FROM users WHERE username IN ('testuser', 'admin');"
    print("\nVerifying fixture users:")
    if not execute_sql_in_k8s(verify_sql, namespace):
        print("Warning: Failed to verify fixture users", file=sys.stderr)

    print("\n✓ Test fixtures populated successfully!")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Populate test fixtures in Kubernetes MySQL database'
    )
    parser.add_argument(
        '--namespace',
        default='arcana-cloud',
        help='Kubernetes namespace (default: arcana-cloud)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print verbose output'
    )

    args = parser.parse_args()

    success = populate_fixtures(namespace=args.namespace, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
