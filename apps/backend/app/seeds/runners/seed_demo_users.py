import asyncio

from seeds.services.seed_demo_user_service import run_seed_demo_users


def main() -> None:
    asyncio.run(run_seed_demo_users())


if __name__ == "__main__":
    main()
