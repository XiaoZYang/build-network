#!/bin/bash
#!/usr/bin/bash

python generate-data.py source|shuf|tr ';' '\n' > generated-log
