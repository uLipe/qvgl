/**
 * @file ir_v1.h
 * QVGL IR v1 — canonical binary layout (little-endian).
 *
 * See docs/04-ir-schema.md and schema/qvglir-v1.schema.json.
 */
#ifndef QVGL_IR_V1_H
#define QVGL_IR_V1_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define QVGLIR_MAGIC   0x31564751u  /* 'Q''V''G''1' */
#define QVGLIR_VERSION 1u

#define QVGL_NODE_NO_PARENT 0xFFFFFFFFu
#define QVGL_STR_NONE       0u

typedef enum {
    QVGL_NODE_ITEM = 0,
    QVGL_NODE_RECTANGLE,
    QVGL_NODE_TEXT,
    QVGL_NODE_IMAGE,
    QVGL_NODE_ARC,
    QVGL_NODE_METER,
    QVGL_NODE_MOUSE_AREA,
    QVGL_NODE_COUNT
} qvgl_node_kind_t;

typedef enum {
    QVGL_VAL_BOOL = 0,
    QVGL_VAL_I32,
    QVGL_VAL_F32,
    QVGL_VAL_COLOR,      /* 0xAARRGGBB */
    QVGL_VAL_STRING,     /* string pool index */
    QVGL_VAL_ENUM,
    QVGL_VAL_BINDING,    /* binding[] index */
    QVGL_VAL_RECT,       /* four f32 in property payload extension */
} qvgl_value_kind_t;

typedef enum {
    QVGL_NODE_F_STATIC_LAYOUT  = 1u << 0,
    QVGL_NODE_F_NEEDS_OBSERVER = 1u << 1,
} qvgl_node_flags_t;

typedef enum {
    QVGL_EXPR_SYM = 0,
    QVGL_EXPR_CONST_I32,
    QVGL_EXPR_CONST_F32,
    QVGL_EXPR_CONST_STR,
    QVGL_EXPR_ADD,
    QVGL_EXPR_SUB,
    QVGL_EXPR_MUL,
    QVGL_EXPR_TERNARY,
    QVGL_EXPR_MAP_LINEAR,
    QVGL_EXPR_FORMAT,
    QVGL_EXPR_COUNT
} qvgl_expr_kind_t;

typedef enum {
    QVGL_SYM_MODULE_PROP = 0,
    QVGL_SYM_NODE_PROP,
} qvgl_sym_kind_t;

typedef struct {
    uint32_t magic;
    uint16_t version;
    uint16_t reserved0;
    uint32_t profile_hash;
    uint32_t module_name;       /* string pool index */
    uint32_t root_node;
    uint32_t str_count;
    uint32_t str_off;
    uint32_t node_count;
    uint32_t node_off;
    uint32_t prop_count;
    uint32_t prop_off;
    uint32_t mod_prop_count;
    uint32_t mod_prop_off;
    uint32_t binding_count;
    uint32_t binding_off;
    uint32_t expr_count;
    uint32_t expr_off;
    uint32_t handler_count;
    uint32_t handler_off;
    uint32_t file_size;
} qvglir_header_t;

typedef struct {
    uint16_t kind;              /* qvgl_node_kind_t */
    uint16_t flags;
    uint32_t name;              /* string index, optional */
    uint32_t id;                /* string index, QVGL_STR_NONE if absent */
    uint32_t parent;
    uint32_t child_first;
    uint16_t child_count;
    uint16_t reserved;
    uint32_t prop_off;
    uint16_t prop_count;
    uint16_t reserved2;
} qvglir_node_t;

typedef struct {
    uint32_t key;               /* string pool */
    uint16_t value_kind;        /* qvgl_value_kind_t */
    uint16_t reserved;
    uint32_t value;             /* inline or index per kind */
} qvglir_property_t;

typedef struct {
    uint32_t name;              /* string pool */
    uint16_t type;              /* qvgl_value_kind_t (f32, i32, bool, string) */
    uint16_t reserved;
    uint32_t default_value;
} qvglir_module_prop_t;

typedef struct {
    uint32_t target_node;
    uint32_t target_key;
    uint32_t expr;
    uint16_t flags;
    uint16_t reserved;
} qvglir_binding_t;

typedef struct {
    uint16_t kind;              /* qvgl_expr_kind_t */
    uint16_t arity;
    uint32_t args[8];           /* indices or literals per kind */
} qvglir_expr_t;

typedef struct {
    uint32_t sym_kind;          /* qvgl_sym_kind_t */
    uint32_t node;              /* for NODE_PROP */
    uint32_t key;               /* string index */
} qvglir_sym_ref_t;

typedef struct {
    uint32_t node;
    uint32_t signal;            /* string: clicked, pressed, … */
    uint32_t handler;           /* string: C symbol */
    uint16_t flags;
    uint16_t reserved;
} qvglir_handler_t;

#ifdef __cplusplus
}
#endif

#endif /* QVGL_IR_V1_H */
