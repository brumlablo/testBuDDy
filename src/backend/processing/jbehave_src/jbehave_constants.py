import os


class JBehaveConstants:
    # --------------------------------SUT folder structure--------------------------------- #
    SUT_SRC_DIR = "src"
    SUT_TEST_DIR = os.path.join(SUT_SRC_DIR, "test")
    module_steps_class_name = "{TEST_MODULE_NAME}_{TEST_MODULE_ID}"

    pom_file_dir = ""
    pom_file_name = "pom.xml"

    runner_dir = os.path.join(SUT_TEST_DIR, "java")
    runner_file_name = "TestbuddyRunnerTest.java"
    runner_file_content = ""
    runner_file_module_add = "stepFileList.add(new {STEPS_MODULE}Steps());\n" \
        .format(STEPS_MODULE=module_steps_class_name) + " "*8
    runner_file_add_module_ending = "/*test-buddy modules - end*/"
    runner_file_module_regex = r'(?:\t\t)*(?:\/\*test\-buddy modules \- start\*\/\n)' \
                               r'((?:.*\n)*)(?:\t\t)*(?:\/\*test\-buddy modules \- end\*\/\n)'

    ci_file_img = "maven:3.6-jdk-11"
    ci_file_variables = "  MAVEN_OPTS: \"-Dorg.slf4j.simpleLogger.log.org.apache.maven.cli.transfer." \
                        "Slf4jMavenTransferListener=WARN -Dorg.slf4j.simpleLogger.showDateTime=true -" \
                        "Djava.awt.headless=true\"\n  MAVEN_CLI_OPTS: \"--batch-mode --errors --fail-a" \
                        "t-end --show-version -DinstallAtEnd=true -DdeployAtEnd=true\""
    ci_file_build_script = "\n    - 'mvn $MAVEN_CLI_OPTS test-compile'"
    ci_file_test_script = "\n    - 'mvn $MAVEN_CLI_OPTS verify'"
    ci_file_test_other = "\n  artifacts:\n    paths:\n      - target/*.jar\n"
    # ---------------------------------------story file------------------------------------ #

    # stories file
    stories_base_dir = os.path.join(SUT_TEST_DIR, "resources", "stories")
    story_dir = "{STEPS_MODULE}".format(STEPS_MODULE=module_steps_class_name)
    story_file_type = ".story"

    # -------------------------------generated code with steps------------------------------ #

    # generated code with steps declarations and empty bodies
    generated_code_dir = os.path.join(SUT_TEST_DIR, "java")
    generated_code_file_type = ".java"
    generated_code_class = "{STEPS_MODULE}Steps".format(STEPS_MODULE=module_steps_class_name)
    generated_code_file_full_name = generated_code_class + generated_code_file_type

    generated_code_head = "import org.jbehave.core.annotations.*;\n" \
                          "import org.jbehave.core.steps.Steps;\n" \
                          "import org.junit.Assert;\n" \
                          "\n" \
                          "/**\n" \
                          " * Testbuddy generated steps file\n" \
                          " * @author testbuddy\n" \
                          " *\n" \
                          " */\n"
    generated_code_class_start = \
        "/*---testbuddy---module---{STEPS_MODULE}---*/\n".format(STEPS_MODULE=module_steps_class_name)\
        + "public class " + generated_code_class + " extends Steps {{ \n\n"

    generated_code_class_end = "}\n"
    generated_code_param_declaration = '''@Named("{PARAM_UNIT_NAME}") {PARAM_UNIT_TYPE} {PARAM_UNIT_NAME}'''
    generated_code_step_comment = "/*---testbuddy---step---{STEP_DEF_ID}---*/"
    generated_code_step_core = "\n\t" + generated_code_step_comment + "\n" \
                               "\t@{GHERKIN_TYPE}(\"{STEP_CONTENT}\")\n" \
                               "\tpublic void {STEP_FUNC_DECL}({STEP_PARAMS}) {{\n" \
                               "\t\tAssert.fail(\"Step not implemented yet.\");\n" \
                               "\t}}\n" \
                               "\t" + generated_code_step_comment + "\n\n"
    runtime_info = ""

    # -------------------------------expected results for reports------------------------------ #
    report_before_stories = "(BeforeStories)"
    report_after_stories = "(AfterStories)"
    report_before_1_story = "Running story "
    report_step_fail = "(FAILED)"
    report_step_not_performed = "(NOT PERFORMED)"
    report_success_check = ["BUILD SUCCESS", "Failures: 0, Errors: 0"]
    report_fail_check = "BUILD FAILURE"
    report_step_base = ["Given", "When", "Then"]

