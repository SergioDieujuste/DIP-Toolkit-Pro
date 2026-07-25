import psutil


def get_disks():

    disks = []

    for partition in psutil.disk_partitions():

        try:

            usage = psutil.disk_usage(partition.mountpoint)

        except PermissionError:
            continue

        disks.append({

            "name": partition.device,
            "mount": partition.mountpoint,
            "filesystem": partition.fstype,
            "total": round(usage.total / (1024**3), 1),
            "used": round(usage.used / (1024**3), 1),
            "free": round(usage.free / (1024**3), 1),
            "percent": int(usage.percent),

        })

    return disks