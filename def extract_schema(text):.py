def extract_schema(text):
    type_map = {
        "string": "s",
        "integer": "i",
        "decimal": "dc",
        "date/time": "d"
    }
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        col_name = parts[0]
        col_type = parts[1].lower()
        mapped_type = type_map.get(col_type, "s")
        result[col_name] = mapped_type

    # Convert dict to required string format
    formatted_text = ",".join(f"{k}:{v}" for k, v in result.items())
    return formatted_text

# --- STEP 1: PASTE YOUR COLUMNS FROM INFORMATICA HERE ---
text = """inst_no string     4000       0              false      
employer_no    integer 4000       0              false      
status    date/time 4000       0              false      
stat_name          string     4000       0              false      
pay_name          decimal 4000       0              false      
addr1    string     4000       0              false      
"""
csv_input = extract_schema(text)

# --- STEP 2: RUN THE SCRIPT ---
columns_and_types = [item.strip().split(":") for item in csv_input.split(",")]

# Group by type
strings = [c[0] for c in columns_and_types if c[1] == "s"]
integers = [c[0] for c in columns_and_types if c[1] == "i"]
dates = [c[0] for c in columns_and_types if c[1] == "d"]
decimals = [c[0] for c in columns_and_types if c[1] == "dc"]

print("// -----------------------------------------------------------")
print("// COPY & PASTE THIS ENTIRE BLOCK INTO INFORMATICA ON INPUT ROW")
print("// -----------------------------------------------------------\n")

print("// --- 1. INITIALIZE DEFAULT VALUES ---")
print("// This handles missing fields and empty JSON strings inherently.")
if strings:
    for s in strings: print(f"{s} = null;")
if integers:
    for i in integers: print(f"{i} = 0;")
if decimals:
    for d in decimals: print(f'{d} = new java.math.BigDecimal("0.0");')
if dates:
    print('java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd\'T\'HH:mm:ss");')
    print('java.util.Date defaultDate = new java.util.Date(0);')
    print('try { defaultDate = sdf.parse("1900-01-01T00:00:00"); } catch (Exception e) {}')
    for d in dates: print(f"{d} = defaultDate;")
print()

print("String jsonText = new String(data);\n")
print("if (jsonText != null && !jsonText.isEmpty()) {")

# 1. STRING GENERATION
if strings:
    print('    // --- EXTRACT STRING FIELDS ---')
    print('    String[] strFields = {"' + '", "'.join(strings) + '"};')
    print('    for (int i = 0; i < strFields.length; i++) {')
    print('        String pStr = "\\"" + strFields[i] + "\\"[ ]*:[ ]*[{][ ]*\\"string\\"[ ]*:[ ]*\\"([^\\"]+)\\"[ ]*[}]";')
    print('        java.util.regex.Matcher m = java.util.regex.Pattern.compile(pStr).matcher(jsonText);')
    print('        if (m.find()) {')
    print('            String val = m.group(1);')
    print('            switch (i) {')
    for i, name in enumerate(strings):
        print(f"                case {i}: {name} = val; break;")
    print('            }')
    print('        }')
    print('    }\n')

# 2. INTEGER GENERATION
if integers:
    print('    // --- EXTRACT INTEGER FIELDS ---')
    print('    String[] intFields = {"' + '", "'.join(integers) + '"};')
    print('    for (int i = 0; i < intFields.length; i++) {')
    print('        String pStr = "\\"" + intFields[i] + "\\"[ ]*:[ ]*[{][ ]*\\"int\\"[ ]*:[ ]*([0-9]+)[ ]*[}]";')
    print('        java.util.regex.Matcher m = java.util.regex.Pattern.compile(pStr).matcher(jsonText);')
    print('        if (m.find()) {')
    print('            int val = Integer.parseInt(m.group(1));')
    print('            switch (i) {')
    for i, name in enumerate(integers):
        print(f"                case {i}: {name} = val; break;")  # FIXED: Assign val, not 0
    print('            }')
    print('        }')
    print('    }\n')

# 3. DECIMAL GENERATION
if decimals:
    print('    // --- EXTRACT DECIMAL FIELDS ---')
    print('    String[] decFields = {"' + '", "'.join(decimals) + '"};')
    print('    for (int i = 0; i < decFields.length; i++) {')
    # Regex updated to capture potential decimals like 12.34
    print('        String pStr = "\\"" + decFields[i] + "\\"[ ]*:[ ]*[{][ ]*\\"decimal\\"[ ]*:[ ]*([0-9]+(?:\\\\.[0-9]+)?)[ ]*[}]";')
    print('        java.util.regex.Matcher m = java.util.regex.Pattern.compile(pStr).matcher(jsonText);')
    print('        if (m.find()) {')
    print('            String valStr = m.group(1);')
    print('            switch (i) {')
    for i, name in enumerate(decimals):
        print(f'                case {i}: {name} = new java.math.BigDecimal(valStr); break;') # FIXED: Assign valStr
    print('            }')
    print('        }')
    print('    }\n')

# 4. DATE GENERATION
if dates:
    print('    // --- EXTRACT DATE FIELDS ---')
    print('    String[] dateFields = {"' + '", "'.join(dates) + '"};')
    print('    for (int i = 0; i < dateFields.length; i++) {')
    print('        String pStr = "\\"" + dateFields[i] + "\\"[ ]*:[ ]*[{][ ]*\\"string\\"[ ]*:[ ]*\\"([^\\"]+)\\"[ ]*[}]";')
    print('        java.util.regex.Matcher m = java.util.regex.Pattern.compile(pStr).matcher(jsonText);')
    print('        if (m.find()) {')
    print('            try {')
    print('                java.util.Date parsedDate = sdf.parse(m.group(1));')
    print('                switch (i) {')
    for i, name in enumerate(dates):
        print(f"                    case {i}: {name} = parsedDate; break;") # FIXED: Assign parsedDate
    print('                }')
    print('            } catch (Exception e) { /* Fallback to defaultDate is already handled */ }')
    print('        }')
    print('    }')

print("}")