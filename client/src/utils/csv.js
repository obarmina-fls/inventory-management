// CSV helpers: RFC 4180 escaping, formula-injection guard, UTF-8 BOM, Blob download.

// Characters that make spreadsheet apps treat a cell as a formula
const FORMULA_PREFIX = /^[=+\-@\t\r]/

// Convert one value to a CSV field.
// null/undefined -> empty; real numbers stay raw (so negatives remain numeric).
export function escapeCsvValue(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : ''
  let str = String(value)
  // Neutralize CSV/formula injection by prefixing an apostrophe (strings only)
  if (FORMULA_PREFIX.test(str)) str = "'" + str
  // Quote when the value contains a comma, quote, CR or LF; double embedded quotes
  if (/[",\r\n]/.test(str)) str = '"' + str.replace(/"/g, '""') + '"'
  return str
}

export function toCsvLine(values) {
  return values.map(escapeCsvValue).join(',')
}

// Build CSV text from headers and rows (arrays of values). CRLF line endings per RFC 4180.
// Pass headers = null to emit rows only.
export function buildCsv(headers, rows) {
  const lines = []
  if (headers) lines.push(toCsvLine(headers))
  for (const row of rows) lines.push(toCsvLine(row))
  return lines.join('\r\n')
}

// Download text as a CSV file. The BOM makes Excel detect UTF-8 (needed for Japanese text).
export function downloadCsv(filename, csvText) {
  const blob = new Blob(['﻿' + csvText], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
