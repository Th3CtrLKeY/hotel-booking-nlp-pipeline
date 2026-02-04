"""
Hotel Email Parser - CLI Interface

Process hotel booking emails and extract structured information.
"""

import sys
import json
import click
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import HotelEmailPipeline


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Hotel Email Parser - Extract booking information from emails."""
    pass


@cli.command()
@click.argument('email_text')
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
@click.option('--config', '-c', default='config/hotel.yaml', help='Path to hotel config')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')
def process(email_text, output, config, pretty):
    """
    Process a single email and output structured JSON.
    
    Example:
        python -m hotel_email_parser process "I need a room for May 10-12, 2026"
    """
    try:
        # Initialize pipeline
        pipeline = HotelEmailPipeline(config)
        
        # Process email
        result = pipeline.process(email_text)
        
        # Format output
        indent = 2 if pretty else None
        json_output = json.dumps(result, indent=indent)
        
        # Write to file or stdout
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            click.echo(f"Result saved to: {output}", err=True)
        else:
            click.echo(json_output)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
@click.option('--config', '-c', default='config/hotel.yaml', help='Path to hotel config')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')
def process_file(input_file, output, config, pretty):
    """
    Process email from a text file.
    
    Example:
        python -m hotel_email_parser process-file email.txt --output result.json
    """
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            email_text = f.read()
        
        # Initialize pipeline
        pipeline = HotelEmailPipeline(config)
        
        # Process email
        result = pipeline.process(email_text, email_id=Path(input_file).stem)
        
        # Format output
        indent = 2 if pretty else None
        json_output = json.dumps(result, indent=indent)
        
        # Write to file or stdout
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            click.echo(f"Processed: {input_file} -> {output}", err=True)
        else:
            click.echo(json_output)
            
    except Exception as e:
        click.echo(f"Error processing {input_file}: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('--output', '-o', default='output', help='Output directory for JSON files')
@click.option('--config', '-c', default='config/hotel.yaml', help='Path to hotel config')
@click.option('--pattern', default='*.txt', help='File pattern to match (default: *.txt)')
def batch(input_dir, output, config, pattern):
    """
    Process multiple email files from a directory.
    
    Example:
        python -m hotel_email_parser batch emails/ --output results/
    """
    try:
        input_path = Path(input_dir)
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all matching files
        files = list(input_path.glob(pattern))
        
        if not files:
            click.echo(f"No files matching '{pattern}' found in {input_dir}", err=True)
            sys.exit(1)
        
        click.echo(f"Processing {len(files)} files...", err=True)
        
        # Initialize pipeline
        pipeline = HotelEmailPipeline(config)
        
        # Process each file
        processed = 0
        failed = 0
        
        for file_path in files:
            try:
                # Read email
                with open(file_path, 'r', encoding='utf-8') as f:
                    email_text = f.read()
                
                # Process
                result = pipeline.process(email_text, email_id=file_path.stem)
                
                # Save result
                output_file = output_path / f"{file_path.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                processed += 1
                
                if processed % 10 == 0:
                    click.echo(f"  Processed {processed}/{len(files)}...", err=True)
                    
            except Exception as e:
                click.echo(f"  Failed to process {file_path.name}: {str(e)}", err=True)
                failed += 1
        
        # Summary
        click.echo(f"\nCompleted: {processed} processed, {failed} failed", err=True)
        click.echo(f"Results saved to: {output_path}", err=True)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', default='config/hotel.yaml', help='Path to hotel config')
def evaluate(config):
    """
    Evaluate pipeline on test set and display metrics.
    
    Example:
        python -m hotel_email_parser evaluate
    """
    try:
        # Run evaluation script
        test_file = Path('data/processed/ground_truth_test.jsonl')
        
        if not test_file.exists():
            click.echo(f"Test file not found: {test_file}", err=True)
            click.echo("Run 'python scripts/split_dataset.py' first to create test set.", err=True)
            sys.exit(1)
        
        click.echo("Running evaluation on test set...\n", err=True)
        
        # Load test data
        test_data = []
        with open(test_file, 'r', encoding='utf-8') as f:
            for line in f:
                test_data.append(json.loads(line))
        
        # Initialize pipeline
        pipeline = HotelEmailPipeline(config)
        
        # Metrics
        intent_correct = 0
        segment_count_correct = 0
        
        for email in test_data:
            result = pipeline.process(email['raw_email'])
            
            if result['intent'] == email['intent']:
                intent_correct += 1
            
            if len(result['segments']) == len(email.get('segments', [])):
                segment_count_correct += 1
        
        # Display results
        total = len(test_data)
        click.echo("=" * 60)
        click.echo("Evaluation Results")
        click.echo("=" * 60)
        click.echo(f"\nTest Set Size: {total} emails")
        click.echo(f"\nIntent Classification: {intent_correct}/{total} ({intent_correct/total*100:.1f}%)")
        click.echo(f"Segment Count: {segment_count_correct}/{total} ({segment_count_correct/total*100:.1f}%)")
        click.echo("\n" + "=" * 60)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
