#!/bin/sh
python -c "import json
from nb_conda_kernels import CondaKernelSpecManager as CKSM
sm = CKSM()
print(json.dumps(sm._conda_info, indent=2))
print(json.dumps(sm.get_all_specs(), indent=2))"
npm install
npm run test
