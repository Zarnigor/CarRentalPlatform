  ## Module structure convention
  
  App modules (models, services, serializers, views) start as single files.
  Convert to a package once an app crosses **5 models** or the file **exceeds ~300 lines**:
  
  - Simple file: geo/, fleet/, accounts/, ops/
  - Package (6 models, complex business logic): bookings/
  
  When converting, re-export everything in `__init__.py` to keep external imports stable.