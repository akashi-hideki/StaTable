ERROR    InvalidDistribution: Cannot find file (or expand pattern): 'dist\statable-3.5.2.tar.gz@ 
         # StaTable v3.5.2                                                                       
                                                                                                 
         **Release date:** 2026-10-11                                                            
         **PyPI:** https://pypi.org/project/statable/3.5.2/                                      
                                                                                                 
         ## Highlights                                                                           
                                                                                                 
         ### Phase 1c complete: mypy 58 -> 0 errors                                              
                                                                                                 
         All mypy errors across 118 source files resolved.                                       
                                                                                                 
         - Annotation-only changes + 2 runtime guards; no behavior change.                       
         - Key fixes:                                                                            
           - xml_io.py (16): ImportError fallback typing, Element                                
             kwargs invariance, int(str | None) guard, append None-guards                        
           - validation_dialog.py (9): PySide6 Qt enum stub suppression                          
             via [[tool.mypy.overrides]]                                                         
           - transition_generator.py (7): Callable[..., str],                                    
             Optional[str] = None                                                                
           - naming_convention.py (6): typed CONVERSION_PATTERNS                                 
           - model.py (4): Union[List[ActionStep], List[str]] for                                
             State.entry / exit / do_actions (backward compat)                                   
           - misc: enum_generator, variable_generator, c_code_generator,                         
             logger, response_parser/validator, prompt_generator                                 
                                                                                                 
         ## Verification                                                                         
                                                                                                 
         - 48 test suites / 1793 PASS / 0 FAIL                                                   
         - mypy: Success: no issues found in 118 source files                                    
                                                                                                 
         ## Installation (PyPI)                                                                  
                                                                                                 
         pip install statable==3.5.2                                                             
                                                                                                 
         ## Related releases                                                                     
                                                                                                 
         - v3.5.1: wheel + sdist (Eclipse Installer added to repository)                         
         - eclipse-installer-v0.1.0: standalone Eclipse Installer ZIP                            
         - v3.5.0: Portable ZIP + S-GUI + Phase 1b                                               
                                                                                                 
         ## Remaining (v3.5.3+)                                                                  
                                                                                                 
         - S-3 Step 2: ubuntu-26.04 preview job (2026-10-19 onwards)                             
         @'                                                                                      
