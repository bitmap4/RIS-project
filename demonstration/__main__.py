import sys
from .protocol_demo import run_protocol_demo
from .security_demo import run_security_demo
from .attack_demo import run_attack_demos


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "protocol"
    
    if mode == "protocol":
        run_protocol_demo()
    elif mode == "security":
        run_security_demo()
    elif mode == "attacks":
        run_attack_demos()
    elif mode == "all":
        print("\n" + "=" * 70)
        print("  RUNNING ALL DEMONSTRATIONS")
        print("=" * 70)
        run_protocol_demo()
        print("\n\n")
        run_security_demo()
        print("\n\n")
        run_attack_demos()
    else:
        print("Usage: python -m demonstration [protocol|security|attacks|all]")
        print("\nModes:")
        print("  protocol - End-to-end protocol execution")
        print("  security - Security features (showing protocol works)")
        print("  attacks  - Critical security flaws (showing vulnerabilities)")
        print("  all      - Run all demonstrations")
        sys.exit(1)


if __name__ == "__main__":
    main()
