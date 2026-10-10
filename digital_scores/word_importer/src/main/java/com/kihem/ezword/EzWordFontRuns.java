package com.kihem.ezword;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import org.apache.poi.hwpf.HWPFDocument;
import org.apache.poi.hwpf.usermodel.CharacterRun;
import org.apache.poi.hwpf.usermodel.Range;

/**
 * Emits one JSON object per legacy-Word character run containing EZ PUA code
 * points. It is an extraction utility only: it does not interpret music and
 * it never writes a Neanes score.
 */
public final class EzWordFontRuns {
  private EzWordFontRuns() {}

  private static String quote(String value) {
    StringBuilder escaped = new StringBuilder("\"");
    for (int index = 0; index < value.length(); index++) {
      char character = value.charAt(index);
      switch (character) {
        case '\\': escaped.append("\\\\"); break;
        case '"': escaped.append("\\\""); break;
        case '\b': escaped.append("\\b"); break;
        case '\f': escaped.append("\\f"); break;
        case '\n': escaped.append("\\n"); break;
        case '\r': escaped.append("\\r"); break;
        case '\t': escaped.append("\\t"); break;
        default:
          if (character < 0x20) {
            escaped.append(String.format("\\u%04x", (int) character));
          } else {
            escaped.append(character);
          }
      }
    }
    return escaped.append('"').toString();
  }

  private static List<Integer> puaCodePoints(String text) {
    List<Integer> result = new ArrayList<>();
    text.codePoints().filter(value -> value >= 0xF000 && value <= 0xF8FF).forEach(result::add);
    return result;
  }

  public static void main(String[] arguments) throws Exception {
    if (arguments.length != 1) {
      System.err.println("Usage: EzWordFontRuns SOURCE.doc");
      System.exit(2);
    }
    Path source = Path.of(arguments[0]);
    try (InputStream input = Files.newInputStream(source); HWPFDocument document = new HWPFDocument(input)) {
      Range range = document.getRange();
      for (int index = 0; index < range.numCharacterRuns(); index++) {
        CharacterRun run = range.getCharacterRun(index);
        String text = run.text();
        List<Integer> pua = puaCodePoints(text);
        if (pua.isEmpty()) {
          continue;
        }
        StringBuilder json = new StringBuilder("{");
        json.append("\"run_index\":").append(index);
        json.append(",\"start_offset\":").append(run.getStartOffset());
        json.append(",\"end_offset\":").append(run.getEndOffset());
        json.append(",\"font_name\":").append(quote(run.getFontName()));
        json.append(",\"font_size_half_points\":").append(run.getFontSize());
        json.append(",\"bold\":").append(run.isBold());
        json.append(",\"italic\":").append(run.isItalic());
        json.append(",\"text\":").append(quote(text));
        json.append(",\"pua_codepoints\":[");
        for (int codeIndex = 0; codeIndex < pua.size(); codeIndex++) {
          if (codeIndex > 0) json.append(',');
          json.append(quote(String.format("U+%04X", pua.get(codeIndex))));
        }
        json.append("]}");
        System.out.println(json);
      }
    }
  }
}
