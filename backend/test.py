import fastf1

  # Get driver info for 2025 season
  driver_info = fastf1.get_driver_info(2025)

  # Print all drivers with their numbers
  for driver_id, info in driver_info.items():
      print(f"#{info['Number']}: {info['FullName']} ({info['Abbreviation']})")

  # Or get as a structured list
  drivers_list = []
  for driver_id, info in driver_info.items():
      drivers_list.append({
          'number': info['Number'],
          'name': info['FullName'],
          'abbreviation': info['Abbreviation']
      })

  # Sort by number
  drivers_list.sort(key=lambda x: int(x['number']))

  for driver in drivers_list:
      print(f"#{driver['number']}: {driver['name']} ({driver['abbreviation']})")
