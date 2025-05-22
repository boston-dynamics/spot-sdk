import sys

from MySpot import MySpot
from coverage import arm_trajectory

import bosdyn.client
import bosdyn.client.util


def main():
    # Parse arguments given
    import argparse
    parser = argparse.ArgumentParser(description='Spot API Test')
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()

    try:
        # Create spot
        robot = MySpot()
        robot.connect(options)
        robot.stow_arm()
        robot.stand_up()

        # Start the state machine
        while True:
            try:
                line = input("Enter 4 floats or a command (l, g, e)").strip()
                # 0.75 0.2 1.0 -0.4 -->  reaches 1.4 m
                # 0.75 0.4 0.8 -0.4 -->  okish

                if line.lower() == "e":
                    print("Exiting loop.")
                    break  # Exit the loop

                if line.lower() == "l":
                    robot.toggle_lease()
                    continue

                if line.lower() == "g":
                    robot.toggle_gripper()
                    continue

                # Split and attempt to convert to floats
                parts = line.split()
                if len(parts) != 4:
                    print("Please enter exactly 4 numbers")
                    continue

                floats = [float(part) for part in parts]
                print(f"Read floats: {floats}")
                arm_trajectory(robot, *floats, 0.2, 0.1)
                robot.stow_arm()
            except ValueError:
                print("Invalid input. Make sure to enter 3 valid float numbers or 'e'.")

        robot.power_off()
    except Exception as exc:
        print(f'Spot threw an exception: {exc}')
        return False
    except KeyboardInterrupt:
        pass

    print('Done!!')


if __name__ == '__main__':
    if not main():
        sys.exit(1)
