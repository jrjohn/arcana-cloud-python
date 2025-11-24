#!/usr/bin/env python3
"""
PEP 8 Refactoring Script
Renames files from PascalCase to snake_case and updates all imports
"""
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List

# File renaming map
FILE_RENAMES = {
    'app/Config.py': 'app/config.py',
    'app/Container.py': 'app/container.py',
    'app/Extensions.py': 'app/extensions.py',
    'app/utils/Exceptions.py': 'app/utils/exceptions.py',
    'app/utils/Response.py': 'app/utils/response.py',
    'app/controllers/AuthController.py': 'app/controllers/auth_controller.py',
    'app/controllers/UserController.py': 'app/controllers/user_controller.py',
    'app/controllers/PublicUserController.py': 'app/controllers/public_user_controller.py',
    'app/services/interfaces/AuthService.py': 'app/services/interfaces/auth_service.py',
    'app/services/interfaces/UserService.py': 'app/services/interfaces/user_service.py',
    'app/services/implementations/AuthServiceImpl.py': 'app/services/implementations/auth_service_impl.py',
    'app/services/implementations/UserServiceImpl.py': 'app/services/implementations/user_service_impl.py',
    'app/services/clients/HTTPAuthServiceClient.py': 'app/services/clients/http_auth_service_client.py',
    'app/services/clients/LoadBalancer.py': 'app/services/clients/load_balancer.py',
    'app/services/clients/ServiceClient.py': 'app/services/clients/service_client.py',
    'app/services/routes/AuthServiceRoutes.py': 'app/services/routes/auth_service_routes.py',
    'app/services/routes/UserServiceRoutes.py': 'app/services/routes/user_service_routes.py',
    'app/services/adapters/UserServiceAdapter.py': 'app/services/adapters/user_service_adapter.py',
    'app/repositories/interfaces/UserRepository.py': 'app/repositories/interfaces/user_repository.py',
    'app/repositories/interfaces/OAuthTokenRepository.py': 'app/repositories/interfaces/oauth_token_repository.py',
    'app/repositories/implementations/UserRepositoryImpl.py': 'app/repositories/implementations/user_repository_impl.py',
    'app/repositories/implementations/OAuthTokenRepositoryImpl.py': 'app/repositories/implementations/oauth_token_repository_impl.py',
    'app/repositories/clients/GRPCUserRepositoryClient.py': 'app/repositories/clients/grpc_user_repository_client.py',
    'app/repositories/clients/HTTPUserRepositoryClient.py': 'app/repositories/clients/http_user_repository_client.py',
    'app/repositories/routes/UserRepositoryRoutes.py': 'app/repositories/routes/user_repository_routes.py',
    'app/schemas/AuthSchema.py': 'app/schemas/auth_schema.py',
    'app/schemas/UserSchema.py': 'app/schemas/user_schema.py',
    'app/decorators/AuthDecorators.py': 'app/decorators/auth_decorators.py',
    'app/decorators/ValidationDecorators.py': 'app/decorators/validation_decorators.py',
    'app/tasks/BackgroundTasks.py': 'app/tasks/background_tasks.py',
    'app/tasks/CeleryWorker.py': 'app/tasks/celery_worker.py',
    'app/tasks/ScheduledTasks.py': 'app/tasks/scheduled_tasks.py',
    'app/tasks/TaskDecorators.py': 'app/tasks/task_decorators.py',
}


def create_import_replacements() -> List[tuple]:
    """Create import replacement patterns"""
    replacements = []

    for old_file, new_file in FILE_RENAMES.items():
        # Convert file paths to import paths
        old_import = old_file.replace('/', '.').replace('.py', '')
        new_import = new_file.replace('/', '.').replace('.py', '')

        # Pattern: from app.X.Y import Z
        replacements.append((
            f'from {old_import} import',
            f'from {new_import} import'
        ))

        # Pattern: import app.X.Y
        replacements.append((
            f'import {old_import}',
            f'import {new_import}'
        ))

    return replacements


def update_file_imports(file_path: str, replacements: List[tuple]) -> bool:
    """Update imports in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply all replacements
        for old, new in replacements:
            content = content.replace(old, new)

        # Only write if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def refactor_files():
    """Execute the refactoring"""
    print("="*80)
    print("PEP 8 Refactoring: Renaming files to snake_case")
    print("="*80)
    print()

    # Step 1: Rename files
    print("STEP 1: Renaming files...")
    print("-"*80)
    renamed_count = 0
    for old_path, new_path in FILE_RENAMES.items():
        if os.path.exists(old_path):
            print(f"  {old_path} → {new_path}")
            shutil.move(old_path, new_path)
            renamed_count += 1
        else:
            print(f"  [SKIP] {old_path} (not found)")

    print(f"\nRenamed {renamed_count} files")
    print()

    # Step 2: Update imports
    print("STEP 2: Updating import statements...")
    print("-"*80)

    replacements = create_import_replacements()

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('app'):
        # Skip __pycache__ and other generated directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache', 'htmlcov']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # Also check test files
    for root, dirs, files in os.walk('tests'):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # Also check root level files
    for file in os.listdir('.'):
        if file.endswith('.py') and os.path.isfile(file):
            python_files.append(file)

    updated_count = 0
    for file_path in python_files:
        if update_file_imports(file_path, replacements):
            print(f"  Updated: {file_path}")
            updated_count += 1

    print(f"\nUpdated {updated_count} files")
    print()

    print("="*80)
    print("Refactoring complete!")
    print("="*80)
    print()
    print("Next steps:")
    print("1. Run tests: pytest tests/")
    print("2. Check for any remaining issues")
    print("3. Commit changes: git add -A && git commit -m 'Refactor: Convert to PEP 8 naming'")
    print()


if __name__ == '__main__':
    import sys

    if '--execute' in sys.argv:
        refactor_files()
    else:
        print("="*80)
        print("PEP 8 Refactoring Preview")
        print("="*80)
        print()
        print("This script will:")
        print(f"1. Rename {len(FILE_RENAMES)} files from PascalCase to snake_case")
        print("2. Update all import statements across the codebase")
        print()
        print("Files to be renamed:")
        for old, new in sorted(FILE_RENAMES.items()):
            print(f"  {old:50} → {new}")
        print()
        print("To execute, run:")
        print("  python3 refactor_to_pep8.py --execute")
        print()
