import asyncio

from seeds.services.seed_work_order_service import run_seed_work_orders


if __name__ == "__main__":
    asyncio.run(run_seed_work_orders())
