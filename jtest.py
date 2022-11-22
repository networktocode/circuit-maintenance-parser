from circuit_maintenance_parser import init_provider, NotificationData

with open("message_eml.eml", "r") as file:
    message = file.read().encode()

provider = init_provider("Cogent")

d2p = NotificationData.init_from_email_bytes(message)

mtnc = provider.get_maintenances(d2p)

print(mtnc)


    
