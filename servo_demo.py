
ANGLES = {
    "LOW": 0,
    "MEDIUM": 90,
    "HIGH": 180
}

def main():

    print("=" * 45)
    print("LOAD-INDICATING E-COMMERCE SIMULATOR")
    print("VIRTUAL SERVO DEMONSTRATION")
    print("=" * 45)

    print("LOW = 0 degrees")
    print("MEDIUM = 90 degrees")
    print("HIGH = 180 degrees")
    print("Type EXIT to stop.\n")

    while True:

        choice = input("Enter load status: ").strip().upper()

        if choice == "EXIT":
            print("Demo stopped.")
            break

        if choice not in ANGLES:
            print("Invalid input. Try LOW, MEDIUM or HIGH.")
            continue

        angle = ANGLES[choice]

        print(f"Load Status: {choice}")
        print(f"Virtual Servo Angle: {angle} degrees")
        print("-" * 35)


if __name__ == "__main__":
    main()
