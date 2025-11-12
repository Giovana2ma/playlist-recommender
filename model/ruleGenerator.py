"""
Association Rules Generator for Spotify Playlist Dataset
Uses Apriori algorithm to mine frequent itemsets and generate association rules.
This code only generates and saves rules - it does NOT make recommendations.

Expected dataset format:
- CSV files with playlists containing songs
- Each row represents a playlist with multiple song columns
"""

import pandas as pd
import pickle
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import argparse
from pathlib import Path
import unicodedata
import string
import sys


class RulesGenerator:
    """
    Generator for association rules using the Apriori algorithm.
    Suitable for playlist recommendation systems.
    """
    
    def __init__(self, min_support=0.01, min_confidence=0.3, min_lift=1.0, max_len=None):
        """
        Initialize the rules generator with threshold parameters.
        
        Args:
            min_support (float): Minimum support threshold for frequent itemsets (default: 0.01)
            min_confidence (float): Minimum confidence threshold for rules (default: 0.3)
            min_lift (float): Minimum lift threshold for rules (default: 1.0)
            max_len (int): Maximum length of itemsets (None = no limit)
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.min_lift = min_lift
        self.max_len = max_len
        self.frequent_itemsets = None
        self.rules = None

    def normalize_track_name(self, track_name):
        track_name = track_name.lower()
        track_name = unicodedata.normalize('NFC', track_name)
        track_name = track_name.strip()
        track_name = track_name.translate(
            str.maketrans('', '', string.punctuation))
        return track_name
        
    def load_spotify_transactions(self, data_path):
        """
        Load Spotify playlist data from CSV file.
        Each row represents a playlist, and columns contain songs in that playlist.
        
        Args:
            data_path (str): Path to the Spotify dataset CSV file
            
        Returns:
            list: List of transactions (playlists), where each transaction is a list of songs
        """
        df = pd.read_csv(data_path)
        df["track_name"] = df["track_name"].apply(self.normalize_track_name)

        itemsets = df.groupby('pid')['track_name'].apply(list).reset_index()
        transactions = itemsets["track_name"].values

        return transactions

    def preprocess_transactions(self, transactions):
        """
        Convert transactions to a one-hot encoded DataFrame suitable for Apriori.
        
        Args:
            transactions (list): List of transactions
            
        Returns:
            pd.DataFrame: One-hot encoded transaction DataFrame
        """
        # Use TransactionEncoder to convert to binary matrix
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df = pd.DataFrame(te_ary, columns=te.columns_)
        return df
    
    def generate_frequent_itemsets(self, df_encoded):
        """
        Generate frequent itemsets using Apriori algorithm.
        
        Args:
            df_encoded (pd.DataFrame): One-hot encoded transaction DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with frequent itemsets and their support
        """
        
            
        self.frequent_itemsets = apriori(
            df_encoded, 
            min_support=self.min_support, 
            use_colnames=True,
            max_len=self.max_len
        )
        
        return self.frequent_itemsets
    
    def generate_rules(self, metric='confidence', min_threshold=None):
        """
        Generate association rules from frequent itemsets.
        
        Args:
            metric (str): Metric to use for rule generation 
                         ('confidence', 'lift', 'support', 'conviction')
            min_threshold (float): Minimum threshold for the metric
            
        Returns:
            pd.DataFrame: DataFrame with association rules and their metrics
        """
        
        if min_threshold is None:
            min_threshold = self.min_confidence if metric == 'confidence' else self.min_lift
            
        self.rules = association_rules(
            self.frequent_itemsets, 
            metric=metric, 
            min_threshold=min_threshold
        )
        
        # Filter by additional criteria
        if metric != 'confidence':
            self.rules = self.rules[self.rules['confidence'] >= self.min_confidence]
        if metric != 'lift':
            self.rules = self.rules[self.rules['lift'] >= self.min_lift]
        
        return self.rules
    
    def save_rules(self, output_path):
        """
        Save the generated rules to a pickle file.
        
        Args:
            output_path (str): Path to save the rules
        """
        if self.rules is None:
            raise ValueError("No rules to save. Generate rules first.")
        
        with open(output_path, 'wb') as f:
            pickle.dump(self.rules, f)
    
    
    def run_pipeline(self, data_path, output_path):
        """
        Run the complete pipeline: load Spotify data, generate itemsets and rules, save.
        This function ONLY generates and saves rules - it does NOT make recommendations.
        
        Args:
            data_path (str): Path to the Spotify dataset CSV file
            output_path (str): Path to save the generated rules (pickle file)
        """
        
        transactions = self.load_spotify_transactions(data_path)
        df_encoded = self.preprocess_transactions(transactions)
        
        self.generate_frequent_itemsets(df_encoded)
        self.generate_rules()

        self.save_rules(output_path)
        
        
        return self.rules


def main():
    """
    Main function for command-line usage.
    This script generates association rules from Spotify playlist data.
    It does NOT make recommendations - only generates and saves rules.
    """
    parser = argparse.ArgumentParser(
        description='Generate association rules from Spotify playlist data using Apriori algorithm.\n'
                    'This tool ONLY generates and saves rules - it does NOT make recommendations.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate rules from ds1 with default parameters
  python rulesGenerator.py /home/datasets/spotify/2023_spotify_ds1.csv
  
  # Generate rules with custom thresholds
  python rulesGenerator.py /home/datasets/spotify/2023_spotify_ds1.csv -s 0.005 -c 0.5 -l 2.0
  
  # Generate rules and save to specific file
  python rulesGenerator.py /home/datasets/spotify/2023_spotify_ds1.csv -o rules_ds1.pkl
  
  # Update model with ds2
  python rulesGenerator.py /home/datasets/spotify/2023_spotify_ds2.csv -o rules_ds2.pkl
        """
    )
    parser.add_argument(
        'input', 
        type=str, 
        help='Path to Spotify dataset CSV file (e.g., 2023_spotify_ds1.csv)'
    )
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default='association_rules.pkl',
        help='Path to output pickle file (default: association_rules.pkl)'
    )
    parser.add_argument(
        '-s', '--min-support', 
        type=float, 
        default=0.05,
        help='Minimum support threshold (default: 0.05). Lower values find more patterns but slower.'
    )
    parser.add_argument(
        '-c', '--min-confidence', 
        type=float, 
        default=0.5,
        help='Minimum confidence threshold (default: 0.5). Higher values = more reliable rules.'
    )
    parser.add_argument(
        '-l', '--min-lift', 
        type=float, 
        default=1.0,
        help='Minimum lift threshold (default: 1.0). Values > 1.0 indicate positive correlation.'
    )
    parser.add_argument(
        '-m', '--max-len',
        type=int,
        default=None,
        help='Maximum length of itemsets (default: None = no limit). Lower values = faster.'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)
    
    # Create generator with specified parameters
    generator = RulesGenerator(
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
        max_len=args.max_len
    )
    
    # Run the pipeline
    try:
        rules = generator.run_pipeline(args.input, args.output)
        if rules is not None and len(rules) > 0:
            sys.exit(0)
        else:
            print("\nNo rules generated. Consider adjusting parameters.")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
