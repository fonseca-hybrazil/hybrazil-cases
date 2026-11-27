// Texto Estruturado (IEC 61131-3), como no CODESYS V2.3 e V3.5.
// Gramática para highlight.js/lowlight. A linguagem não diferencia maiúsculas de minúsculas.
import type { HLJSApi, Language } from 'highlight.js'

// Listas conferidas com a ajuda oficial do CODESYS V3.5 (content.helpme-codesys.com, palavras-chave e
// erro C0543) e com o manual do CoDeSys V2.3.8 (apêndices B, C e E).

// Declaração e estrutura (V2.3 + V3)
const ESTRUTURA = [
  'PROGRAM', 'END_PROGRAM', 'FUNCTION', 'END_FUNCTION', 'FUNCTION_BLOCK', 'END_FUNCTION_BLOCK',
  'ACTION', 'END_ACTION', 'TYPE', 'END_TYPE', 'STRUCT', 'END_STRUCT',
  'VAR', 'VAR_INPUT', 'VAR_OUTPUT', 'VAR_IN_OUT', 'VAR_GLOBAL', 'VAR_EXTERNAL', 'VAR_CONFIG', 'VAR_ACCESS',
  'VAR_CONSTANT', 'END_VAR', 'CONSTANT', 'RETAIN', 'PERSISTENT', 'AT', 'ARRAY', 'OF', 'POINTER', 'TO',
  'READ_ONLY', 'READ_WRITE',
]

// Somente V3: orientação a objetos e extensões
const ESTRUTURA_V3 = [
  'METHOD', 'END_METHOD', 'PROPERTY', 'END_PROPERTY', 'INTERFACE', 'END_INTERFACE', 'EXTENDS', 'IMPLEMENTS',
  'UNION', 'END_UNION', 'REFERENCE', 'VAR_TEMP', 'VAR_INST', 'VAR_STAT', 'PUBLIC', 'PRIVATE', 'PROTECTED',
  'INTERNAL', 'ABSTRACT', 'FINAL', 'PARAMS', 'USING', 'CLASS',
]

// Controle de fluxo (CONTINUE e JMP em ST só no V3; ELSEIF é reservado no V2.3)
const FLUXO = [
  'IF', 'THEN', 'ELSIF', 'ELSEIF', 'ELSE', 'END_IF', 'CASE', 'END_CASE', 'FOR', 'BY', 'DO', 'END_FOR',
  'WHILE', 'END_WHILE', 'REPEAT', 'UNTIL', 'END_REPEAT', 'EXIT', 'RETURN', 'CONTINUE', 'JMP',
  '__TRY', '__CATCH', '__FINALLY', '__ENDTRY',
]

// Operadores em palavra
const OPERADORES = ['AND', 'OR', 'XOR', 'NOT', 'MOD', 'AND_THEN', 'OR_ELSE']

// Tipos elementares
const TIPOS = [
  'BOOL', 'BIT', 'BYTE', 'WORD', 'DWORD', 'LWORD', 'SINT', 'USINT', 'INT', 'UINT', 'DINT', 'UDINT', 'LINT', 'ULINT',
  'REAL', 'LREAL', 'STRING', 'WSTRING', 'TIME', 'LTIME', 'DATE', 'LDATE', 'TIME_OF_DAY', 'TOD', 'LTOD', 'LTIME_OF_DAY',
  'DATE_AND_TIME', 'DT', 'LDT', 'LDATE_AND_TIME', '__XWORD', '__UXINT', '__XINT',
  'ANY', 'ANY_NUM', 'ANY_INT', 'ANY_REAL', 'ANY_BIT', 'ANY_STRING', 'ANY_DATE', 'ANY_ELEMENTARY', 'ANY_MAGNITUDE',
  'ANY_DERIVED', 'ANY_SIGNED', 'ANY_UNSIGNED', 'ANY_DURATION', 'ANY_CHARS', 'ANY_CHAR', 'CHAR', 'WCHAR',
]

const LITERAIS = ['TRUE', 'FALSE', 'THIS', 'SUPER']

// Blocos e funções padrão (IEC + operadores do CODESYS)
const NATIVOS = [
  // blocos de função
  'TON', 'TOF', 'TP', 'LTON', 'LTOF', 'LTP', 'R_TRIG', 'F_TRIG', 'CTU', 'CTD', 'CTUD', 'SR', 'RS', 'RTC', 'SEMA',
  // funções numéricas
  'ABS', 'SQRT', 'LN', 'LOG', 'EXP', 'EXPT', 'SIN', 'COS', 'TAN', 'ASIN', 'ACOS', 'ATAN', 'ATAN2', 'TRUNC',
  'TRUNC_INT', 'ROUND',
  // seleção e bits
  'SEL', 'MAX', 'MIN', 'LIMIT', 'MUX', 'MOVE', 'SHL', 'SHR', 'ROL', 'ROR',
  // texto
  'LEN', 'LEFT', 'RIGHT', 'MID', 'CONCAT', 'INSERT', 'DELETE', 'REPLACE', 'FIND',
  // operadores do CODESYS
  'SIZEOF', 'ADR', 'ADRINST', 'BITADR', 'INDEXOF', 'INI', 'CAL', 'XSIZEOF', '__NEW', '__DELETE', '__ISVALIDREF',
  '__QUERYINTERFACE', '__QUERYPOINTER', '__POUNAME', '__POSITION', '__POOL', '__COMPARE_AND_SWAP',
  '__XADD', 'TEST_AND_SET',
]

const ESPECIFICADORES = 'PUBLIC|PRIVATE|PROTECTED|INTERNAL|ABSTRACT|FINAL'

export default function st(hljs: HLJSApi): Language {
  const COMENTARIOS = [
    hljs.COMMENT(/\(\*/, /\*\)/, { contains: ['self'] }),   // (* ... *), aninhável no V3
    hljs.COMMENT(/\/\*/, /\*\//),                             // /* ... */ (V3)
    hljs.C_LINE_COMMENT_MODE,                                 // // ... (V3)
  ]
  const ESCAPE = { scope: 'char.escape', match: /\$(?:[0-9A-Fa-f]{2,4}|[$'"LlNnPpRrTt])/ }
  return {
    name: 'Texto Estruturado (IEC 61131-3)',
    aliases: ['iecst', 'codesys', 'scl'],
    case_insensitive: true,
    keywords: {
      $pattern: '[A-Za-z_][A-Za-z0-9_]*',   // inclui __NEW, END_IF, R_TRIG
      keyword: [...ESTRUTURA, ...ESTRUTURA_V3, ...FLUXO, ...OPERADORES],
      type: TIPOS,
      literal: LITERAIS,
      built_in: NATIVOS,
    },
    contains: [
      ...COMENTARIOS,
      // pragmas e atributos: {attribute 'qualified_only'}, {IF defined(X)}, {warning '...'}
      { scope: 'meta', begin: /\{/, end: /\}/, contains: [{ scope: 'string', begin: /'/, end: /'/ }] },
      { scope: 'string', begin: /'/, end: /'/, contains: [ESCAPE] },    // STRING
      { scope: 'string', begin: /"/, end: /"/, contains: [ESCAPE] },    // WSTRING
      // caractere: UCHAR#'x' (V3)
      { scope: 'string', match: /\bW?UCHAR#'(?:\$.|[^'])'/ },
      // literais de tempo/data: T#1s500ms, TIME#5m, LTIME#..., D#2024-01-31, DT#..., TOD#12:00:00
      {
        scope: 'number',
        match: /\b(?:L?TIME|L?T|L?DATE|L?D|L?DATE_AND_TIME|L?DT|L?TIME_OF_DAY|L?TOD)#[0-9A-Za-z_:.+-]+/,
        relevance: 5,
      },
      // literais com base ou tipados: 16#FF, 2#1010_0101, 8#17, INT#5, REAL#1.5
      { scope: 'number', match: /\b(?:[A-Z_]+#)?(?:2|8|16)#[0-9A-Fa-f_]+\b/, relevance: 5 },
      { scope: 'number', match: /\b[A-Z_]+#[+-]?[0-9][0-9_.eE+-]*/, relevance: 2 },
      { scope: 'number', match: /\b[0-9][0-9_]*(?:\.[0-9_]+)?(?:[eE][+-]?[0-9]+)?\b/, relevance: 0 },
      // endereços diretos: %IX0.0, %QW4, %MD10, %I*
      { scope: 'variable', match: /%[IQM][XBWDL]?(?:\*|[0-9]+(?:\.[0-9]+)*)/, relevance: 5 },
      // conversões de tipo: INT_TO_REAL, TO_INT, DWORD_TO_TIME ...
      { scope: 'built_in', match: /\b(?:[A-Z_]+_)?TO_[A-Z_]+\b/, relevance: 2 },
      // atribuições e operadores simbólicos
      { scope: 'operator', match: /:=|=>|\bS=|\bR=|\bREF=|<>|<=|>=|\*\*|\^/, relevance: 0 },
      // nome da POU: FUNCTION_BLOCK FB_Motor, METHOD PUBLIC Reset, PROPERTY FINAL Valor ...
      {
        scope: 'title',
        match: new RegExp(
          '(?<=\\b(?:PROGRAM|FUNCTION_BLOCK|FUNCTION|METHOD|PROPERTY|INTERFACE|ACTION)\\s+(?:(?:' + ESPECIFICADORES + ')\\s+)*)'
          + '(?!(?:' + ESPECIFICADORES + ')\\b)[A-Za-z_][A-Za-z0-9_]*',
        ),
      },
    ],
  }
}
