Here is the complete redundancy analysis across all 5 files:                                               
                                                                                                             
  ---                                                                                     
  Redundancy Analysis Report                                                                                 
                                                                                                             
  Who runs what and when?
                                                                                                             
  ┌───────────────────────────────────────────────┬───────────────────────────────┬─────────────────────┐    
  │                     File                      │            Trigger            │  Runs on migrate?   │    
  ├───────────────────────────────────────────────┼───────────────────────────────┼─────────────────────┤    
  │ custom_fields.py                              │ ensure_custom_fields() in     │ Yes — every bench   │ 
  │                                               │ install.py                    │ migrate             │ 
  ├───────────────────────────────────────────────┼───────────────────────────────┼─────────────────────┤    
  │ install.py                                    │ setup_enhanced_print_settings │ Yes (via ensure_cus │    
  │ create_enhanced_print_settings_fields()       │ () → fresh install path       │ tom_fields)         │    
  ├───────────────────────────────────────────────┼───────────────────────────────┼─────────────────────┤    
  │ install.py migrate_existing_print_settings()  │ setup_enhanced_print_settings │ Yes (if fields      │ 
  │                                               │ () → migration path           │ already exist)      │    
  ├───────────────────────────────────────────────┼───────────────────────────────┼─────────────────────┤ 
  │ install_watermark_fields.py                   │ Manual: bench                 │ No — manual only    │    
  │                                               │ install-watermark-fields      │                     │    
  ├───────────────────────────────────────────────┼───────────────────────────────┼─────────────────────┤ 
  │ erpnext_install.py                            │ Never called directly         │ No                  │    
  │                                               │ (monkey-patched away)         │                     │    
  ├───────────────────────────────────────────────┼───────────────────────────────┼─────────────────────┤
  │ patches/v1_2/ensure_watermark_fields_complete │ One-time patch (already ran)  │ No                  │    
  │ .py                                           │                               │                     │
  └───────────────────────────────────────────────┴───────────────────────────────┴─────────────────────┘

  ---                                                                                                        
  Field-level conflicts (Print Settings watermark fields)
                                                                                                             
  Field: watermark_font_size                                                                              
  install.py (fresh path): Data, default "24px"                                                              
  install_watermark_fields.py (correct): Int, default 24                                                     
  Risk: ⚠️  Wrong type on fresh install                                                                       
  ────────────────────────────────────────                                                                   
  Field: watermark_font_family                                                                               
  install.py (fresh path): Select, default "Arial"                                                        
  install_watermark_fields.py (correct): Select, default "Kanit"                                             
  Risk: Wrong default on fresh install                                                                       
  ────────────────────────────────────────                                                                
  Field: watermark_position                                                                                  
  install.py (fresh path): Select, 9 options, correct                                                        
  install_watermark_fields.py (correct): Select, 9 options                                                
  Risk: OK                                                                                                   
  ────────────────────────────────────────                                                                   
  Field: watermark_settings                                                                              
  install.py (fresh path): Long description                                                                  
  install_watermark_fields.py (correct): Empty description                                               
  Risk: Minor                                                                                                
  ────────────────────────────────────────                                                                   
  Field: watermark_col_break
  install.py (fresh path): MISSING                                                                           
  install_watermark_fields.py (correct): Column Break                                              
  Risk: No 2-column layout on fresh install
  ────────────────────────────────────────
  Field: watermark_margin_top/right/bottom/left
  install.py (fresh path): MISSING
  install_watermark_fields.py (correct): 4× Int, default 0
  Risk: ⚠️  Margin fields never created on fresh install

  Also: setup_default_print_settings_values() (line 1294) sets watermark_font_size = "12px" if empty — a     
  string going into an Int field on conflict.
                                                                                                             
  ---                                                                                              
  Execution order risk on bench migrate
                                       
  Every bench migrate calls ensure_custom_fields() → setup_enhanced_print_settings():
  - If fields already exist → migrate_existing_print_settings() → only fixes depends_on on 3 fields,         
  otherwise safe                                                                                             
  - If fresh install → create_enhanced_print_settings_fields() → creates Data watermark_font_size, no margin 
  fields                                                                                                     
                                                                                                             
  So a fresh install that has never run bench install-watermark-fields will have wrong field types and no 
  margin fields. The _migrate_legacy_fields() in install_watermark_fields.py handles the Data→Int migration, 
  but only when the command is run manually.                                                       
                                                                                                             
  ---                                                                                              
  erpnext_install.py status
                                                                                                             
  Effectively dead code — monkey_patch_erpnext() redirects ERPNext's function to
  create_enhanced_print_settings_fields(). The original create_print_setting_custom_fields() in              
  erpnext_install.py is never called. Same stale definitions: Data font_size "24px", Arial, 5 positions only.
                                                                                                             
  ---                                                                                              
  patches/v1_2/ensure_watermark_fields_complete.py status
                                                                                                             
  Already ran once. Missing: 4 directional margin fields, column break, Kanit default. Has Arial and "12" as
  Int for font_size — at least the correct type. Harmless going forward since patches run once.              
                                                                                                          
  ---                                                                                                        
  Verdict: 3 actionable problems                                                                          
                                                                                                             
  Problem 1 (High risk): create_enhanced_print_settings_fields() in install.py creates watermark_font_size as
   Data type and has no margin fields. Any fresh install that skips the manual command gets broken watermark.
                                                                                                          
  Problem 2 (Medium risk): setup_default_print_settings_values() sets font_size to "12px" (string) and       
  font_family to "Sarabun" fallback — wrong vs current canonical values of 24 and Kanit.                  
                                                                                                             
  Problem 3 (Low risk): Copy fields in create_enhanced_print_settings_fields() define default_copy_count,    
  copy_labels_column, default_original_label, default_copy_label — these don't exist in
  install_watermark_fields.py at all, but they likely work fine since they're not watermark-related.         
                                                                                                          
  ---    
  Recommended fix (minimal)
                                                                                                             
  Update create_enhanced_print_settings_fields() in install.py to call
  _install_print_settings_watermark_fields() from install_watermark_fields.py instead of redefining the      
  watermark section inline. Also update setup_default_print_settings_values() to use 24 (Int) and "Kanit" as
  defaults.                                                                                                  
                                                                                                          
  Want me to apply these fixes?                                                                              
  
● Ran 3 stop hooks (ctrl+o to expand)                                                                        
  ⎿  Stop hook error: Failed with non-blocking status code: /bin/sh: 1: bun: not found                    
  ⎿  Stop hook error: Failed with non-blocking status code: /bin/sh: 1: bun: not found
                                                                                                             
✻ Sautéed for 3m 46s · 1 shell still running
                                                                                                             
❯ Yes just make sure it don't break our code
