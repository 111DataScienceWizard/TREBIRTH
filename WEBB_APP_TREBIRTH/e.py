/home/adminuser/venv/lib/python3.12/site-packages/streamlit/runtime/scriptrunner/exec_code.py:88 in exec_func_with_error_handling                         
  /home/adminuser/venv/lib/python3.12/site-packages/streamlit/runtime/scriptrunner/script_runner.py:590 in code_to_exec                                     
/mount/src/trebirth/WEBB_APP_TREBIRTH/w2.py:186 in <module>                   
183 │   │   │   processed_list.append(df)                                   
    184 │   │   return pd.concat(processed_list, axis=1)                        
  ❱ 186 │   df_radar = process_data(radar_data, 'Radar ')                       
    187 │   #df_adxl = process_data(adxl_data, 'ADXL ')                         
    188 │   df_ax = process_data(ax_data, 'Ax ')                                
    189 │   df_ay = process_data(ay_data, 'Ay ')                                
/mount/src/trebirth/WEBB_APP_TREBIRTH/w2.py:182 in process_data               
    179 │   │   │   df = pd.DataFrame(data).dropna()                            
    180 │   │   │   df.fillna(df.mean(), inplace=True)                          
    181 │   │   │   new_columns = [f'{prefix}{i}']                              
  ❱ 182 │   │   │   df.columns = new_columns                                    
    183 │   │   │   processed_list.append(df)                                   
    184 │   │   return pd.concat(processed_list, axis=1)                        
    185                                                                         
  /home/adminuser/venv/lib/python3.12/site-packages/pandas/core/generic.py:631  
  3 in __setattr__                                                              
     6310 │   │                                                                 
     6311 │   │   try:                                                          
     6312 │   │   │   object.__getattribute__(self, name)                       
  ❱  6313 │   │   │   return object.__setattr__(self, name, value)              
     6314 │   │   except AttributeError:                                        
     6315 │   │   │   pass                                                      
     6316                                                                       
  in pandas._libs.properties.AxisProperty.__set__:69                            
  /home/adminuser/venv/lib/python3.12/site-packages/pandas/core/generic.py:814  
  in _set_axis                                                                  
      811 │   │   directly, e.g. `series.index = [1, 2, 3]`.                    
      812 │   │   """                                                           
      813 │   │   labels = ensure_index(labels)                                 
  ❱   814 │   │   self._mgr.set_axis(axis, labels)                              
      815 │   │   self._clear_item_cache()                                      
      816 │                                                                     
      817 │   @final                                                            
  /home/adminuser/venv/lib/python3.12/site-packages/pandas/core/internals/mana  
  gers.py:238 in set_axis                                                       
     235 │                                                                      
     236 │   def set_axis(self, axis: AxisInt, new_labels: Index) -> None:      
     237 │   │   # Caller is responsible for ensuring we have an Index object.  
  ❱  238 │   │   self._validate_set_axis(axis, new_labels)                      
     239 │   │   self.axes[axis] = new_labels                                   
     240 │                                                                      
     241 │   @property                                                          
  /home/adminuser/venv/lib/python3.12/site-packages/pandas/core/internals/base  
  .py:98 in _validate_set_axis                                                  

     95 │   │   │   pass                                                        
     96 │   │                                                                   
     97 │   │   elif new_len != old_len:                                        
  ❱  98 │   │   │   raise ValueError(                                           
     99 │   │   │   │   f"Length mismatch: Expected axis has {old_len} element  
    100 │   │   │   │   f"values have {new_len} elements"                       
    101 │   │   │   )                                                           
────────────────────────────────────────────────────────────────────────────────
ValueError: Length mismatch: Expected axis has 0 elements, new values have 1 
elements
2024-09-09 11:58:19.812 503 GET /script-health-check (127.0.0.1) 3691.55ms
