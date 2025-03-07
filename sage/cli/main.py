"""Command line interface for SAGE."""
import argparse
import os
import sys
from typing import List, Optional

from ..processors.yaml_processor import YAMLProcessor
from ..processors.package_processor import PackageProcessor
from ..processors.sender_processor import SenderProcessor
from ..utils.logger import get_logger

logger = get_logger(__name__)

def validate_yaml(args) -> int:
    """Validate a YAML file."""
    processor = YAMLProcessor()
    success, errors = processor.validate_yaml(args.yaml_path, args.schema_type)

    if success:
        logger.info("✅ YAML validation successful")
        return 0
    else:
        logger.error("\nValidation errors:")
        for error in errors:
            logger.error(f"❌ {error}")
        return 1

def process_package(args) -> int:
    """Process a package ZIP file."""
    processor = PackageProcessor()
    success, errors = processor.process_package(
        args.zip_path,
        args.package_yaml,
        args.catalogs_dir,
        args.force  # Nuevo parámetro para forzar procesamiento
    )

    if success:
        logger.info("✅ Package processed successfully")
        return 0
    else:
        logger.error("\nProcessing errors:")
        for error in errors:
            if "Paquete duplicado" in error:
                logger.warning(f"⚠️  {error}")
                logger.info("Use --force to process anyway if the file is newer")
            else:
                logger.error(f"❌ {error}")
        return 1

def validate_sender(args) -> int:
    """Validate a sender configuration."""
    processor = SenderProcessor()
    success, errors = processor.process_sender(
        args.sender_yaml,
        args.package_name
    )

    if success:
        logger.info("✅ Sender validation successful")
        return 0
    else:
        logger.error("\nValidation errors:")
        for error in errors:
            logger.error(f"❌ {error}")
        return 1

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='SAGE CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Validate YAML command
    validate_parser = subparsers.add_parser('validate-yaml', help='Validate a YAML file')
    validate_parser.add_argument('yaml_path', help='Path to YAML file')
    validate_parser.add_argument(
        'schema_type',
        choices=['catalog', 'package', 'sender'],
        help='Type of YAML schema'
    )

    # Process package command
    package_parser = subparsers.add_parser('process-package', help='Process a package ZIP file')
    package_parser.add_argument('zip_path', help='Path to ZIP file')
    package_parser.add_argument('package_yaml', help='Path to package YAML')
    package_parser.add_argument('catalogs_dir', help='Directory containing catalog YAMLs')
    package_parser.add_argument(
        '--force', 
        action='store_true',
        help='Force processing even if package appears to be duplicate'
    )

    # Validate sender command
    sender_parser = subparsers.add_parser('validate-sender', help='Validate a sender configuration')
    sender_parser.add_argument('sender_yaml', help='Path to sender YAML')
    sender_parser.add_argument('package_name', help='Name of the package')

    args = parser.parse_args(argv)

    # Execute the appropriate command
    if args.command == 'validate-yaml':
        return validate_yaml(args)
    elif args.command == 'process-package':
        return process_package(args)
    elif args.command == 'validate-sender':
        return validate_sender(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())