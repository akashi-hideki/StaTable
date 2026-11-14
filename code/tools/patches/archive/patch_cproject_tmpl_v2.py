"""patch_cproject_tmpl_v2.py

Write a valid Eclipse 4.41 ARM Cross GCC .cproject template.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "eclipse_installer" / "templates" / "cproject.tmpl"

T = "\t"

header = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<?fileVersion 4.0.0?>'
    '<cproject storage_type_id="org.eclipse.cdt.core.XmlProjectDescriptionStorage">\n'
    + T + '<storageModule moduleId="org.eclipse.cdt.core.settings">\n'
)

# Debug + Release configurations share most attributes; generate both
def make_config(config_name, config_id, is_release):
    opt_level = (
        "ilg.gnuarmeclipse.managedbuild.cross.option.optimization.level.size"
        if is_release else
        "ilg.gnuarmeclipse.managedbuild.cross.option.optimization.level.none"
    )
    debug_level = (
        ""
        if is_release else
        ' value="ilg.gnuarmeclipse.managedbuild.cross.option.debugging.level.max" valueType="enumerated"'
    )
    return (
        T*2 + f'<cconfiguration id="ilg.gnuarmeclipse.managedbuild.cross.config.elf.{config_name.lower()}.{config_id}">\n'
        + T*3 + f'<storageModule buildSystemId="org.eclipse.cdt.managedbuilder.core.configurationDataProvider" id="ilg.gnuarmeclipse.managedbuild.cross.config.elf.{config_name.lower()}.{config_id}" moduleId="org.eclipse.cdt.core.settings" name="{config_name}">\n'
        + T*4 + '<externalSettings/>\n'
        + T*4 + '<extensions>\n'
        + T*5 + '<extension id="org.eclipse.cdt.core.GNU_ELF" point="org.eclipse.cdt.core.BinaryParser"/>\n'
        + T*5 + '<extension id="org.eclipse.cdt.core.GASErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>\n'
        + T*5 + '<extension id="org.eclipse.cdt.core.GmakeErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>\n'
        + T*5 + '<extension id="org.eclipse.cdt.core.GLDErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>\n'
        + T*5 + '<extension id="org.eclipse.cdt.core.CWDLocator" point="org.eclipse.cdt.core.ErrorParser"/>\n'
        + T*5 + '<extension id="org.eclipse.cdt.core.GCCErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>\n'
        + T*4 + '</extensions>\n'
        + T*3 + '</storageModule>\n'
        + T*3 + '<storageModule moduleId="cdtBuildSystem" version="4.0.0">\n'
        + T*4 + f'<configuration artifactName="${{ProjName}}" buildArtefactType="org.eclipse.cdt.build.core.buildArtefactType.exe" buildProperties="org.eclipse.cdt.build.core.buildArtefactType=org.eclipse.cdt.build.core.buildArtefactType.exe,org.eclipse.cdt.build.core.buildType=org.eclipse.cdt.build.core.buildType.{config_name.lower()}" cleanCommand="${{cross_rm}} -rf" description="" id="ilg.gnuarmeclipse.managedbuild.cross.config.elf.{config_name.lower()}.{config_id}" name="{config_name}" parent="ilg.gnuarmeclipse.managedbuild.cross.config.elf.{config_name.lower()}">\n'
        + T*5 + f'<folderInfo id="ilg.gnuarmeclipse.managedbuild.cross.config.elf.{config_name.lower()}.{config_id}." name="/" resourcePath="">\n'
        + T*6 + f'<toolChain id="ilg.gnuarmeclipse.managedbuild.cross.toolchain.elf.{config_name.lower()}.{config_id}" name="Arm Cross GCC" superClass="ilg.gnuarmeclipse.managedbuild.cross.toolchain.elf.{config_name.lower()}">\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.addtools.createflash" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.addtools.createflash" value="true" valueType="boolean"/>\n'
        + T*7 + f'<option id="ilg.gnuarmeclipse.managedbuild.cross.option.optimization.level" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.optimization.level" value="{opt_level}" valueType="enumerated"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.optimization.functionsections" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.optimization.functionsections" value="true" valueType="boolean"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.optimization.datasections" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.optimization.datasections" value="true" valueType="boolean"/>\n'
        + T*7 + f'<option id="ilg.gnuarmeclipse.managedbuild.cross.option.debugging.level" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.debugging.level"{debug_level}/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.toolchain.name" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.toolchain.name" value="xPack GNU Arm Embedded GCC" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.architecture" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.architecture" value="ilg.gnuarmeclipse.managedbuild.cross.option.architecture.arm" valueType="enumerated"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.arm.target.family" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.arm.target.family" value="ilg.gnuarmeclipse.managedbuild.cross.option.arm.target.mcpu.cortex-m4" valueType="enumerated"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.arm.target.instructionset" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.arm.target.instructionset" value="ilg.gnuarmeclipse.managedbuild.cross.option.arm.target.instructionset.thumb" valueType="enumerated"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.prefix" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.prefix" value="arm-none-eabi-" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.c" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.c" value="gcc" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.cpp" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.cpp" value="g++" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.ar" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.ar" value="ar" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.objcopy" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.objcopy" value="objcopy" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.objdump" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.objdump" value="objdump" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.size" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.size" value="size" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.make" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.make" value="make" valueType="string"/>\n'
        + T*7 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.command.rm" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.command.rm" value="rm" valueType="string"/>\n'
        + T*7 + f'<targetPlatform archList="all" binaryParser="org.eclipse.cdt.core.GNU_ELF" id="ilg.gnuarmeclipse.managedbuild.cross.targetPlatform" isAbstract="false" osList="all" superClass="ilg.gnuarmeclipse.managedbuild.cross.targetPlatform"/>\n'
        + T*7 + f'<builder buildPath="${{workspace_loc:/@@PROJECT_NAME@@}}/Debug" id="ilg.gnuarmeclipse.managedbuild.cross.builder" managedBuildOn="false" name="Gnu Make Builder.{config_name}" superClass="ilg.gnuarmeclipse.managedbuild.cross.builder"/>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.assembler" name="GNU Arm Cross Assembler" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.assembler">\n'
        + T*8 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.assembler.usepreprocessor" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.assembler.usepreprocessor" value="true" valueType="boolean"/>\n'
        + T*8 + '<inputType id="ilg.gnuarmeclipse.managedbuild.cross.tool.assembler.input" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.assembler.input"/>\n'
        + T*7 + '</tool>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.c.compiler" name="GNU Arm Cross C Compiler" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.c.compiler">\n'
        + T*8 + '<inputType id="ilg.gnuarmeclipse.managedbuild.cross.tool.c.compiler.input" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.c.compiler.input"/>\n'
        + T*7 + '</tool>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.cpp.compiler" name="GNU Arm Cross C++ Compiler" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.cpp.compiler"/>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.c.linker" name="GNU Arm Cross C Linker" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.c.linker">\n'
        + T*8 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.c.linker.gcsections" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.c.linker.gcsections" value="true" valueType="boolean"/>\n'
        + T*8 + '<inputType id="ilg.gnuarmeclipse.managedbuild.cross.tool.c.linker.input" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.c.linker.input">\n'
        + T*9 + '<additionalInput kind="additionalinputdependency" paths="$(USER_OBJS)"/>\n'
        + T*9 + '<additionalInput kind="additionalinput" paths="$(LIBS)"/>\n'
        + T*8 + '</inputType>\n'
        + T*7 + '</tool>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.cpp.linker" name="GNU Arm Cross C++ Linker" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.cpp.linker">\n'
        + T*8 + '<option id="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.gcsections" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.linker.gcsections" value="true" valueType="boolean"/>\n'
        + T*7 + '</tool>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.archiver" name="GNU Arm Cross Archiver" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.archiver"/>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.createflash" name="GNU Arm Cross Create Flash Image" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.createflash"/>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.createlisting" name="GNU Arm Cross Create Listing" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.createlisting"/>\n'
        + T*7 + '<tool id="ilg.gnuarmeclipse.managedbuild.cross.tool.printsize" name="GNU Arm Cross Print Size" superClass="ilg.gnuarmeclipse.managedbuild.cross.tool.printsize"/>\n'
        + T*6 + '</toolChain>\n'
        + T*5 + '</folderInfo>\n'
        + T*4 + '</configuration>\n'
        + T*3 + '</storageModule>\n'
        + T*3 + '<storageModule moduleId="org.eclipse.cdt.core.externalSettings"/>\n'
        + T*2 + '</cconfiguration>\n'
    )

body = header
body += make_config("Debug", "1305738145", is_release=False)
body += make_config("Release", "1648457704", is_release=True)
body += T + '</storageModule>\n'
body += T + '<storageModule moduleId="cdtBuildSystem" version="4.0.0">\n'
body += T*2 + '<project id="@@PROJECT_NAME@@.ilg.gnuarmeclipse.managedbuild.cross.target.elf" name="Executable" projectType="ilg.gnuarmeclipse.managedbuild.cross.target.elf"/>\n'
body += T + '</storageModule>\n'
body += T + '<storageModule moduleId="org.eclipse.cdt.core.LanguageSettingsProviders"/>\n'
body += '</cproject>\n'

P.write_text(body, encoding="utf-8")
print(f"[OK] {P}")
print(f"[INFO] tab bytes: {P.read_bytes().count(9)}")
