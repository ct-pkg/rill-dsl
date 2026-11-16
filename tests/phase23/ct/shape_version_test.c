/* PH-23-T3：CT loader 必须拒绝宿主注入的 v1 形状。
 *
 * 这是一个只链接 ct/build/librill_core.a 的裸 C 单测：手工搭一棵带
 * `FnDef` 的树（形状缺 shape_version，span 2:1），调用 load_shapes。
 * 断言它 longjmp 并输出 E-LOAD-FN-SHAPE-VERSION 的诊断信封。
 *
 * 编译与运行见 tests/phase23/test_ct_shape_version.py。
 */

#include "common.h"
#include "loader.h"

static struct JVal *slot(const char *role)
{
    struct JVal *node = jobj();
    jput(node, "role", jstr(role));
    return node;
}

static struct JVal *variable(const char *name)
{
    struct JVal *node = jobj();
    jput(node, "kind", jstr("Variable"));
    jput(node, "name", jstr(name));
    return node;
}

int main(void)
{
    struct JVal *tree;
    struct JVal *headers;
    struct JVal *header;
    struct JVal *defs;
    struct JVal *definition;
    struct JVal *shape;
    struct JVal *template_;
    struct JVal *call;
    struct JVal *body;
    struct JVal *span;
    struct StdoutEmitter out;

    if (setjmp(*fail_jmp_slot()) != 0) {
        out.failed = 0;
        emitter_emit(&out, 0, 0);
        return 0;
    }

    call = jobj();
    jput(call, "kind", jstr("VerbCall"));
    jput(call, "subject", jnull());
    jput(call, "verb", jstr("read"));
    jput(call, "object", variable("p"));
    jput(call, "post", jarr());

    template_ = jarr();
    jpush(template_, call);

    body = jobj();
    jput(body, "kind", jstr("Block"));
    jput(body, "body", jarr());

    /* v1 形状：故意不带 shape_version，模拟宿主注入的旧形状。 */
    shape = jobj();
    jput(shape, "verb", jstr("read"));
    jput(shape, "subject", slot("none"));
    jput(shape, "object", slot("param"));
    jput(shape, "preps", jarr());
    jput(shape, "adverbs", jarr());

    span = jobj();
    jput(span, "line", jint(2));
    jput(span, "col", jint(1));

    definition = jobj();
    jput(definition, "kind", jstr("FnDef"));
    jput(definition, "shape", shape);
    jput(definition, "template", template_);
    jput(definition, "body", body);
    jput(definition, "span", span);

    defs = jarr();
    jpush(defs, definition);

    header = jobj();
    jput(header, "kind", jstr("FnBlock"));
    jput(header, "defs", defs);

    headers = jarr();
    jpush(headers, header);

    tree = jobj();
    jput(tree, "headers", headers);
    jput(tree, "body", jarr());

    load_shapes(tree);
    printf("NOFAIL\n");
    return 1;
}
