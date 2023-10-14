def main():
    import time
    from psetup import config

    setup = config.from_yaml()
    print(setup)
    timestamp = time.strftime("%Y-%m-%dT%H-%M", time.localtime())
    print(timestamp)

main()