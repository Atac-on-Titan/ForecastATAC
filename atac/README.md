# Purpose
The purpose of the package is to expose some of the static data provided by atac.

# Stops
You can query for a stop by its stop ID using the `StopManager`. The manager needs to be created with a path to the ATAC
`stops.txt` file. In the example below, the file is in `data/stops.txt`.

You can query with a single ID, or a list of IDs.
```python
from atac import StopManager

stop_manager = StopManager('data/stops.txt')

id_to_find = "00213"
stop = stop_manager.find_stop(id_to_find)

ids_to_find = ["00213", "04972"]
stops = stop_manager.find_stop(ids_to_find)
```

Alternatively you can also create the Manager from a `pandas` dataframe.

```python
import pandas as pd
from atac import StopManager

stop_manager = StopManager(pd.read_csv('data/stops.txt'))
```

# Trips
The `TripManager` loads ATAC trip data. It can be created with a `trips.txt` file, a list of `Trip` objects, or from a
`pandas` dataframe.

```python
import pandas as pd
from atac import TripManager

TripManager('data/trips.txt')
TripManager(pd.read_csv('data/trips.txt'))
```