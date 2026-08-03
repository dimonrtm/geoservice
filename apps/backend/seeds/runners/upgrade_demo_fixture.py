import asyncio

from seeds.services.demo_fixture_upgrade_service import run_upgrade_demo_fixture


if __name__ == "__main__":
    asyncio.run(run_upgrade_demo_fixture())
