// Private PE identity and bounded PowerPC entrypoint probe.
// Do not export reconstructed PE bytes, instruction bytes, or decompiled code.
// @category DOTM
import ghidra.app.script.GhidraScript;
import ghidra.app.util.Option;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryBlock;
import com.google.gson.GsonBuilder;
import xexloaderwv.XEXHeader;

import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class DotmPhase2Probe extends GhidraScript {
    private static int u16(byte[] data, int offset) {
        if (offset < 0 || offset > data.length - 2) throw new IllegalArgumentException("u16 outside image");
        return (data[offset] & 0xff) | ((data[offset + 1] & 0xff) << 8);
    }
    private static long u32(byte[] data, int offset) {
        return (long)u16(data, offset) | ((long)u16(data, offset + 2) << 16);
    }
    private static String hex(long value, int width) {
        return String.format("0x%0" + width + "X", value);
    }
    private static String sha256(byte[] bytes) throws Exception {
        byte[] hash = MessageDigest.getInstance("SHA-256").digest(bytes);
        StringBuilder sb = new StringBuilder(hash.length * 2);
        for (byte b : hash) sb.append(String.format("%02x", b & 0xff));
        return sb.toString();
    }
    private static boolean has(byte[] data, int pos, byte[] expected) {
        if (pos < 0 || ((long)pos + expected.length) > data.length) return false;
        for (int i = 0; i < expected.length; i++) if (data[pos + i] != expected[i]) return false;
        return true;
    }
    private static void ensure(boolean yes, String why) {
        if (!yes) throw new IllegalStateException(why);
    }
    private Map<String, Object> executableBlocks() {
        List<Map<String, Object>> blocks = new ArrayList<>();
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("name", block.getName());
            item.put("start", block.getStart().toString());
            item.put("end", block.getEnd().toString());
            item.put("executable", block.isExecute());
            item.put("initialized", block.isInitialized());
            blocks.add(item);
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("blocks", blocks);
        return out;
    }
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 3 || currentProgram == null)
            throw new IllegalArgumentException("Expected output JSON, input path, mode");
        final Path output = Path.of(args[0]);
        final Path source = Path.of(args[1]);
        final String mode = args[2];
        ensure(mode.equals("xex") || mode.equals("synthetic"), "Unexpected probe mode");
        ensure(Files.isRegularFile(source), "Input is not a regular file");
        ensure(currentProgram.getLanguageID().getIdAsString().equals("PowerPC:BE:64:A2ALT-32addr"),
               "Ghidra imported the wrong processor");
        ensure(currentProgram.getLanguage().isBigEndian(), "Expected big-endian PowerPC");
        byte[] input = Files.readAllBytes(source);
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("schema_version", 2);
        report.put("kind", mode);
        report.put("source_sha256", sha256(input));
        report.put("source_size_bytes", input.length);
        report.put("language_id", currentProgram.getLanguageID().getIdAsString());
        report.put("full_auto_analysis_performed", false);
        report.put("native_pc_execution_tested", false);
        report.put("disassembly_scope", "single-entrypoint");
        report.put("ghidra_executable_format", currentProgram.getExecutableFormat());
        report.put("memory_summary", executableBlocks());
        Address entry;
        if (mode.equals("xex")) {
            ensure(has(input, 0, new byte[]{0x58, 0x45, 0x58, 0x32}), "Source XEX2 magic missing");
            ensure(currentProgram.getExecutableFormat().equals("XEX Loader by Warranty Voider"),
                   "Ghidra did not use XEXLoaderWV");
            // Use the pinned importer's in-memory reconstruction, without writing it to disk.
            XEXHeader xex = new XEXHeader(input, new ArrayList<Option>(), false);
            byte[] pe = xex.peImage;
            ensure(pe != null && pe.length >= 0x100, "XEX loader did not reconstruct a PE-sized image");
            ensure(has(pe, 0, new byte[]{0x4d, 0x5a}), "Decrypted image has no MZ signature");
            long ntOffset = u32(pe, 0x3c);
            ensure(ntOffset >= 0x40 && ntOffset <= pe.length - 24, "Invalid PE NT header offset");
            int nt = (int)ntOffset;
            ensure(has(pe, nt, new byte[]{0x50, 0x45, 0, 0}), "Missing PE\\0\\0 signature");
            int machine = u16(pe, nt + 4);
            int count = u16(pe, nt + 6);
            int optionalSize = u16(pe, nt + 20);
            ensure(machine != 0, "PE machine type is empty");
            ensure(count > 0 && count <= 96, "PE section count outside guarded range");
            ensure(optionalSize >= 64, "PE optional header too small");
            long tableEnd = ntOffset + 24L + optionalSize + count * 40L;
            ensure(tableEnd <= pe.length, "PE section directory exceeds reconstructed image");
            int magic = u16(pe, nt + 24);
            ensure(magic == 0x010b, "Expected a 32-bit PE optional header");
            long entryRva = u32(pe, nt + 24 + 16);
            long peBase = u32(pe, nt + 24 + 28);
            long sizeOfImage = u32(pe, nt + 24 + 56);
            long xexBase = Integer.toUnsignedLong(xex.imageBaseAddress);
            long xexEntry = Integer.toUnsignedLong(xex.entryPointAddress);
            ensure(peBase == xexBase, "PE image base disagrees with XEX image base");
            ensure(xexEntry >= xexBase, "XEX entry is below image base");
            ensure(xexEntry < xexBase + (long)pe.length, "XEX entry outside recovered image");
            ensure(sizeOfImage != 0 && sizeOfImage <= pe.length, "PE size-of-image is outside recovered image");
            List<Map<String, Object>> sections = new ArrayList<>();
            int executableSections = 0;
            for (int i = 0; i < count; i++) {
                int sp = nt + 24 + optionalSize + 40 * i;
                StringBuilder sectionName = new StringBuilder();
                for (int j = 0; j < 8 && pe[sp + j] != 0; j++)
                    sectionName.append((char)(pe[sp + j] & 0xff));
                long virtualSize = u32(pe, sp + 8);
                long rva = u32(pe, sp + 12);
                long characteristics = u32(pe, sp + 36);
                ensure(rva <= pe.length && virtualSize <= pe.length - rva,
                       "PE section outside reconstructed image");
                boolean executable = (characteristics & 0x20000000L) != 0;
                if (executable) executableSections++;
                Map<String, Object> section = new LinkedHashMap<>();
                section.put("name", sectionName.toString());
                section.put("rva", hex(rva, 8));
                section.put("virtual_size_bytes", virtualSize);
                section.put("executable", executable);
                sections.add(section);
            }
            ensure(executableSections > 0, "No executable PE section");
            report.put("mz_verified", true);
            report.put("pe_signature_verified", true);
            report.put("pe_machine_hex", hex(machine, 4));
            report.put("pe_optional_magic", hex(magic, 4));
            report.put("pe_nt_header_offset", ntOffset);
            report.put("pe_image_length_bytes", pe.length);
            report.put("pe_size_of_image_bytes", sizeOfImage);
            report.put("pe_image_base", hex(peBase, 8));
            report.put("pe_entry_rva", hex(entryRva, 8));
            report.put("xex_image_base", hex(xexBase, 8));
            report.put("xex_entry_point", hex(xexEntry, 8));
            report.put("pe_sections", sections);
            report.put("executable_section_count", executableSections);
            report.put("recovered_pe_sha256_private", sha256(pe));
            entry = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(xexEntry);
            MemoryBlock block = currentProgram.getMemory().getBlock(entry);
            ensure(block != null && block.isInitialized() && block.isExecute(),
                   "XEX entry not mapped in initialized executable memory");
            report.put("entry_in_executable_memory", true);
            report.put("pe_entry_matches_xex_entry", (peBase + entryRva) == xexEntry);
        } else {
            // Only the four-byte synthetic blr fixture is permitted in public CI.
            ensure(input.length == 4 && has(input, 0, new byte[]{0x4e, (byte)0x80, 0, 0x20}),
                   "Synthetic fixture must be the original four-byte blr");
            MemoryBlock block = currentProgram.getMemory().getBlocks()[0];
            entry = block.getStart();
            report.put("mz_verified", false);
            report.put("pe_signature_verified", false);
            report.put("entry_in_executable_memory", false);
        }
        Instruction inst = currentProgram.getListing().getInstructionAt(entry);
        if (inst == null) {
            disassemble(entry);
            inst = currentProgram.getListing().getInstructionAt(entry);
        }
        ensure(inst != null && inst.getLength() == 4, "No four-byte PPC instruction decoded at entry");
        report.put("entry_instruction_decoded", true);
        report.put("entry_instruction_address", entry.toString());
        // Deliberately do not serialize instruction bytes or game disassembly.
        try (Writer writer = Files.newBufferedWriter(output, StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            new GsonBuilder().setPrettyPrinting().create().toJson(report, writer);
        }
        println("DOTM bounded Phase 2 metadata completed; no code bytes exported.");
    }
}
