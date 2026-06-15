import asyncio

from seeds.services.seed_utility_dataset_service import run_seed_utility_dataset


def main() -> None:
    asyncio.run(run_seed_utility_dataset())


if __name__ == "__main__":
    main()
