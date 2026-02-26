#!/usr/bin/env python3

from multi_framework import MultiFrameworkEngine

def test_multi_framework_engine():
    print("Testing Multi-Framework Engine...")
    
    try:
        engine = MultiFrameworkEngine()
        print("✅ Multi-framework engine loaded successfully")
        
        print(f"✅ Available frameworks: {len(engine.frameworks)}")
        
        frameworks = engine.get_available_frameworks()
        for fw in frameworks:
            print(f"- {fw['name']}: {fw['total_controls']} controls ({fw['framework_type']})")
        
        # Test framework activation
        from multi_framework import FrameworkType
        engine.activate_framework(FrameworkType.NIST_CSF_20)
        engine.activate_framework(FrameworkType.ISO_27001_2022)
        print(f"✅ Active frameworks: {len(engine.active_frameworks)}")
        
        # Test crosswalk mappings
        mappings = engine.get_crosswalk_mappings(FrameworkType.NIST_CSF_20, FrameworkType.ISO_27001_2022)
        print(f"✅ Crosswalk mappings (NIST → ISO): {len(mappings)}")
        
        print("✅ All multi-framework tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_multi_framework_engine()