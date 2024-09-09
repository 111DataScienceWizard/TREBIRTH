/home/adminuser/venv/lib/python3.12/site-packages/streamlit/runtime/scriptru  

  nner/exec_code.py:88 in exec_func_with_error_handling                         

                                                                                

  /home/adminuser/venv/lib/python3.12/site-packages/streamlit/runtime/scriptru  

  nner/script_runner.py:590 in code_to_exec                                     

                                                                                

  /mount/src/trebirth/WEBB_APP_TREBIRTH/w2.py:348 in <module>                   

                                                                                

    345 │                                                                       

    346 │   # Add data for each scan to the filtered columns dictionary         

    347 │   for i in range(10):  # Assuming there are 10 scans                  

  ❱ 348 │   │   filtered_radar_columns[f'Radar {i}'] = df_combined_detrended[f  

    349 │   │   #filtered_adxl_columns[f'ADXL {i}'] = df_combined_detrended[f'  

    350 │                                                                       

    351 │   # Apply the process function on each column                         

                                                                                

  /home/adminuser/venv/lib/python3.12/site-packages/pandas/core/frame.py:4102   

  in __getitem__                                                                

                                                                                

     4099 │   │   if is_single_key:                                             

     4100 │   │   │   if self.columns.nlevels > 1:                              

     4101 │   │   │   │   return self._getitem_multilevel(key)                  

  ❱  4102 │   │   │   indexer = self.columns.get_loc(key)                       

     4103 │   │   │   if is_integer(indexer):                                   

     4104 │   │   │   │   indexer = [indexer]                                   

     4105 │   │   else:                                                         

                                                                                

  /home/adminuser/venv/lib/python3.12/site-packages/pandas/core/indexes/base.p  

  y:3812 in get_loc                                                             

                                                                                

    3809 │   │   │   │   and any(isinstance(x, slice) for x in casted_key)      

    3810 │   │   │   ):                                                         

    3811 │   │   │   │   raise InvalidIndexError(key)                           

  ❱ 3812 │   │   │   raise KeyError(key) from err                               

    3813 │   │   except TypeError:                                              

    3814 │   │   │   # If we have a listlike key, _check_indexing_error will r  

    3815 │   │   │   #  InvalidIndexError. Otherwise we fall through and re-ra  

────────────────────────────────────────────────────────────────────────────────

KeyError: 'Radar 4'

2024-09-09 13:44:43.955 503 GET /script-health-check (127.0.0.1) 60039.18ms

2024-09-09 13:45:44.311 503 GET /script-health-check (127.0.0.1) 60080.40ms

2024-09-09 13:46:44.742 503 GET /script-health-check (127.0.0.1) 60099.09ms
