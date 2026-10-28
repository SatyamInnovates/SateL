from pathlib import Path
import psutil
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume 
from comtypes import CLSCTX_ALL 
from ctypes import cast, POINTER

# print(Path.home())


# def get_battery():
#     battery = psutil.sensors_battery()
    
#     return battery[0]


# print(get_battery())

# devices = AudioUtilities.GetSpeakers()

# interface = devices.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)


# volume = cast(interface, POINTER(IAudioEndpointVolume))



# print(volume)



from pycaw.pycaw import AudioUtilities


# Get the default audio output device
devices = AudioUtilities.GetSpeakers()

# Get the volume controller directly
volume = devices.EndpointVolume


# Increase volume by 5%
def volume_up():
    current = volume.GetMasterVolumeLevelScalar()
    new_volume = min(1.0, current + 0.05)

    volume.SetMasterVolumeLevelScalar(new_volume, None)
    print(f"Volume: {round(new_volume * 100)}%")


# Decrease volume by 5%
def volume_down():
    current = volume.GetMasterVolumeLevelScalar()
    new_volume = max(0.0, current - 0.05)

    volume.SetMasterVolumeLevelScalar(new_volume, None)
    print(f"Volume: {round(new_volume * 100)}%")


# Toggle mute/unmute
def mute():
    current_mute = volume.GetMute()
    new_mute = not current_mute

    volume.SetMute(new_mute, None)
    print("Muted" if new_mute else "Unmuted")


# Set volume to a specific percentage
def set_volume(level):
    if not 0 <= level <= 100:
        print("Enter a volume between 0 and 100.")
        return

    volume.SetMasterVolumeLevelScalar(level / 100, None)
    print(f"Volume set to {level}%")


# Display current volume
def get_volume():
    current = volume.GetMasterVolumeLevelScalar()
    muted = volume.GetMute()

    print(f"Current volume: {round(current * 100)}%")
    print(f"Muted: {'Yes' if muted else 'No'}")


# Interactive menu
while True:
    print("\n===== VOLUME CONTROLLER =====")
    print("1. Volume Up (+5%)")
    print("2. Volume Down (-5%)")
    print("3. Mute / Unmute")
    print("4. Set Volume (0-100)")
    print("5. Check Volume")
    print("6. Exit")

    choice = input("Choose an option: ").strip()

    if choice == "1":
        volume_up()

    elif choice == "2":
        volume_down()

    elif choice == "3":
        mute()

    elif choice == "4":
        try:
            level = int(input("Enter volume (0-100): "))
            set_volume(level)
        except ValueError:
            print("Enter a valid integer.")

    elif choice == "5":
        get_volume()

    elif choice == "6":
        print("Volume controller closed.")
        break

    else:
        print("Invalid choice. Select 1-6.")
