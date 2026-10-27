from contextbase_runtime.cli import main as agent_main
from .agent import BehaviorAgent


def main(argv=None):
    return agent_main(BehaviorAgent, argv)


if __name__ == '__main__':
    raise SystemExit(main())
