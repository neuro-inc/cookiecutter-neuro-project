import argparse


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sample training script")
    parser.add_argument("-d", "--data_dir", required=True, help="Path to the dataset")
    return parser


def train(args: argparse.Namespace) -> None:
    print(f"Your training script here. Data directory: {args.data_dir}")


if __name__ == "__main__":
    args = get_parser().parse_args()
    train(args)
