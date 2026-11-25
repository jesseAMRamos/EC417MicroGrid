from pathlib import Path
import typhoon.api.hil as hil
from typhoon.api.schematic_editor import model as model

TSE = Path(r"test.tse")
CPD = TSE.parent / f"{TSE.stem} Target files" / f"{TSE.stem}.cpd"
model.create_new_model(str(TSE))
print("Does this work?")

src = model.create_component("core/Voltage Source", name="V1", position=(8000, 8000))
tl  = model.create_component("core/Transmission Line", name="TL1", position=(8300, 8600))
rl  = model.create_component("core/Resistor", name="Rload", position=(8600, 8000))
gnd = model.create_component("core/Ground", name="GND", position=(8300, 8300))
bus1 = model.create_component("core/Three-phase Meter", name="Meter1", position=(9000, 8200))


model.set_property_value(model.prop(rl,"resistance"),100.0)
model.set_property_value(model.prop(tl,"model"),"PI")
print(model.get_property_values(tl))   # find the real property names, then set them below
# e.g. model.set_property_value(model.prop(tl, "<phases property>"), 1)

t = model.term
model.create_connection(t(src, "p_node"), t(tl, "a_in"))
model.create_connection(t(tl, "a_out"),  t(rl, "p_node"))
model.create_connection(t(rl, "n_node"), t(gnd, "node"))
model.create_connection(t(src, "n_node"), t(gnd, "node"))
# only if Model = PI:
model.create_connection(t(tl, "gnd"), t(gnd, "node"))

model.save_as(str(TSE))
print("Saved:", TSE, TSE.exists())

def create_bus(busNum, pos: tuple[int, int], gen=True, load=True, genConfig=[], loadConfig = []):
    meter = model.create_component("core/Three-phase Meter",name = f"meter #{busNum}", position=pos)
    if gen:
        generator = model.create_component("core/Diesel Genset", name=f"gen #{busNum}", position=(pos[0]+300, pos[1]))
        model.set_property_value(model.prop(generator, "Vref"), 1)# in per unit
        model.set_property_value(model.prop(generator, "Pref"),genConfig[1])#power reference
        model.set_property_value(model.prop(generator, "pf_ref"),genConfig[2])#power factor reference
        model.set_property_value(model.prop(generator, "Gen_OP_mode"),2)#sets are grid forming
        model.set_property_value(model.prop(generator, "wref"), 1) #mechanchal angluar speed in pu
        model.create_connection(model.term(generator, "p_node"), model.term(meter, "a"))
        model.create_connection(model.term(generator, "n_node"), model.term(meter, "n"))
    if load:
        load = model.create_component("core/Three-phase Variable Load", name = load[0], pos = (pos[0]+600,pos(1)))
        #look into load config