from pathlib import Path
import typhoon.api.hil as hil
from typhoon.api.schematic_editor import model as model
from typhoon.api.schematic_editor.const import ITEM_TERMINAL

TSE = Path(r"test.tse")
CPD = TSE.parent / f"{TSE.stem} Target files" / f"{TSE.stem}.cpd"
model.create_new_model(str(TSE))
print("Does this work?")
Vpu = 100,000

#src = model.create_component("core/Voltage Source", name="V1", position=(8000, 8000))
#tl  = model.create_component("core/Transmission Line", name="TL1", position=(8300, 8600))
#rl  = model.create_component("core/Resistor", name="Rload", position=(8600, 8000))
gnd = model.create_component("core/Ground", name="GND", position=(8300, 8300))
#bus1 = model.create_component("core/Three-phase Meter", name="Meter1", position=(9000, 8200))


#model.set_property_value(model.prop(rl,"resistance"),100.0)
#model.set_property_value(model.prop(tl,"model"),"PI")
#print(model.get_property_values(tl))   # find the real property names, then set them below
# e.g. model.set_property_value(model.prop(tl, "<phases property>"), 1)

t = model.term
connection = model.create_connection
#model.create_connection(t(src, "p_node"), t(tl, "a_in"))
#model.create_connection(t(tl, "a_out"),  t(rl, "p_node"))
#model.create_connection(t(rl, "n_node"), t(gnd, "node"))
#model.create_connection(t(src, "n_node"), t(gnd, "node"))
# only if Model = PI:
#model.create_connection(t(tl, "gnd"), t(gnd, "node"))

order = (("","Gen_On"),("1","Vref"), ("2","wref"),("3","Pref"),("4","pf_ref"),("5","Gen_OP_mode"),("6","Gen_Control_mode"),("7","Load_share_on"),("8","Load_share"))
def add_const(name, value, position=(0, 0)):
    c = model.create_component("core/Constant", name=name, position=position)
    model.set_property_value(model.prop(c, "value"), value)
    return c

def create_bus(busNum:int, pos: tuple[int, int], gen=False, load=False, genConfig=[], loadConfig = []):
    #Gen order = (("","Gen_On"),("1","Vref"), ("2","wref"),("3","Pref"),("4","pf_ref"),("5","Gen_OP_mode"),
    # ("6","Gen_Control_mode"),("7","Load_share_on"),("8","Load_share"))
    meter = model.create_component("core/Three-phase Meter",name = f"meter #{busNum}", position=pos)
    gnd = model.create_component("core/Ground", name="GND", position=(pos[0], pos[1]+500))
    generator = None
    powerLoad = None
    if gen:
        try: 
            generator = model.create_component("core/Diesel Genset", name=f"gen #{busNum}", position=(pos[0]-500, pos[1]+300))
            
            #print("Generator properties:", model.get_property_values(generator))
            #print("Generator terminals:", [model.get_name(t) for t in model.get_items(generator, item_type=ITEM_TERMINAL)])
            #print("Meter terminals:", [model.get_name(t) for t in model.get_items(meter, item_type=ITEM_TERMINAL)])
        except Exception as e:
            print("failed to create generator",repr(e))

        try:
            SIGNALS = ["Gen_On", "Vref", "wref", "Pref", "pf_ref",
           "Gen_OP_mode", "Gen_Control_mode", "Load_share_on", "Load_share"]

            values = {
                "Gen_On": 1,
                "Vref": 1,
                "wref": 1,
                "Pref": genConfig[1],
                "pf_ref": genConfig[2],
                "Gen_OP_mode": 2,
                "Gen_Control_mode": 0,   # placeholder: check what values this expects
                "Load_share_on": 0,
                "Load_share": 0,
            }

            gen_input = model.create_component("core/Bus Join", name=f"GenConfig #{busNum}",
                                            position=(pos[0] - 150, pos[1] + 300))
            model.set_property_value(model.prop(gen_input, "inputs"), len(SIGNALS))

            for i, sig in enumerate(SIGNALS):
                c = add_const(f"{sig} #{busNum}", values[sig],
                  (pos[0] - 200, pos[1] + 300 + 60 * i))
                term_name = "in" if i == 0 else f"in{i}"
                model.create_connection(model.term(c, "out"), model.term(gen_input, term_name))

            model.create_connection(model.term(gen_input, "out"), model.term(generator, "Inputs"))
            model.set_property_value(model.prop(generator, "Vn"), Vpu*1)# in per unit
            #model.set_property_value(model.prop(generator, "Pref"),genConfig[1])#power reference
            #model.set_property_value(model.prop(generator, "pf_ref"),genConfig[2])#power factor reference
            #model.set_property_value(model.prop(generator, "Gen_OP_mode"),2)#sets are grid forming
            #model.set_property_value(model.prop(generator, "wref"), 1) #mechanchal angluar speed in pu
        except Exception as e:
            print("Faild to set generator config",repr(e))

        try: 
            model.create_connection(model.term(generator, "A"), model.term(meter, "A+"))
            model.create_connection(model.term(generator, "B"), model.term(meter,"B+"))
            model.create_connection(model.term(generator, "C"), model.term(meter,"C+"))
            model.create_connection(t(meter,"GND"),t(gnd,"node"))
            
        except Exception as e:
            print("failed to create generator connections",repr(e))
    if load:
        try:
            powerLoad = model.create_component("core/Three-phase Variable Load", name = loadConfig[0],
                                                position = (pos[0]+300,pos[1]+300))
        except Exception as e:
            print("Error Creating Load",repr(e))

        try:
            pass
        except Exception as e:
            print("Issue Configuring Load",repr(e))

        try:
            connection(t(powerLoad,"A"),t(meter,"A-"))
            connection(t(powerLoad,"B"),t(meter,"B-"))
            connection(t(powerLoad,"C"),t(meter,"C-"))
        except Exception as e:
            print("error making connections",repr(e))
        #look into load config
    return (meter,generator,powerLoad)
meter3, gen3, load3 = create_bus(3,(9000,9000),gen=True,genConfig=[1,1.05,1.01,1,0.95,2,1,1,0],
                                load=True,loadConfig=["Load3"])
model.save_as(str(TSE))
print("Saved:", TSE, TSE.exists())