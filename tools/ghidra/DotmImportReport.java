// Metadata only. Does not export program bytes, instructions or decompiled code.
// @category DOTM
import ghidra.app.script.GhidraScript;
import ghidra.app.util.opinion.Loader;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.util.classfinder.ClassSearcher;
import com.google.gson.GsonBuilder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.io.Writer;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class DotmImportReport extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1 || currentProgram == null) {
            throw new IllegalArgumentException("Expected a current program and one new JSON output path");
        }
        boolean loaderPresent = false;
        for (Loader loader : ClassSearcher.getInstances(Loader.class)) {
            if (loader.getClass().getName().equals("xexloaderwv.XEXLoaderWVLoader")) {
                loaderPresent = true;
            }
        }
        if (!loaderPresent) {
            throw new IllegalStateException("Pinned XEXLoaderWV extension was not discovered");
        }
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("schema_version", 1);
        report.put("xex_loader_discovered", loaderPresent);
        report.put("language_id", currentProgram.getLanguageID().getIdAsString());
        report.put("big_endian", currentProgram.getLanguage().isBigEndian());
        report.put("address_space_bits", currentProgram.getAddressFactory().getDefaultAddressSpace().getSize());
        report.put("executable_format", currentProgram.getExecutableFormat());
        report.put("executable_sha256", currentProgram.getExecutableSHA256());
        report.put("image_base", currentProgram.getImageBase().toString());
        report.put("imported_function_count", currentProgram.getFunctionManager().getFunctionCount());
        report.put("full_auto_analysis_requested", false);
        report.put("decompilation_performed", false);
        report.put("native_pc_execution_tested", false);
        List<String> entries = new ArrayList<>();
        AddressIterator it = currentProgram.getSymbolTable().getExternalEntryPointIterator();
        while (it.hasNext()) entries.add(it.next().toString());
        report.put("entry_points", entries);
        report.put("external_libraries", currentProgram.getExternalManager().getExternalLibraryNames());
        List<Map<String, Object>> blocks = new ArrayList<>();
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("name", block.getName());
            item.put("start", block.getStart().toString());
            item.put("end", block.getEnd().toString());
            item.put("size_bytes", block.getSize());
            item.put("read", block.isRead());
            item.put("write", block.isWrite());
            item.put("execute", block.isExecute());
            item.put("initialized", block.isInitialized());
            blocks.add(item);
        }
        report.put("memory_blocks", blocks);
        Path out = Path.of(args[0]);
        try (Writer writer = Files.newBufferedWriter(out, StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            new GsonBuilder().setPrettyPrinting().create().toJson(report, writer);
        }
        println("DOTM metadata report written; no decompilation or PC runtime claim.");
    }
}
