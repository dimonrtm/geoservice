import asyncio

from services.demo_user_seed_service import run_demo_user_seed


def main() -> None:
    asyncio.run(run_demo_user_seed())


if __name__ == "__main__":
    main()
