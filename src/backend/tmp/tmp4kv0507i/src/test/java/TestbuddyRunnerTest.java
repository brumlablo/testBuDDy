import java.text.SimpleDateFormat;
import java.util.*;

import org.jbehave.core.configuration.Configuration;
import org.jbehave.core.configuration.MostUsefulConfiguration;
import org.jbehave.core.embedder.PropertyBasedEmbedderControls;
import org.jbehave.core.io.CodeLocations;
import org.jbehave.core.io.LoadFromClasspath;
import org.jbehave.core.io.StoryFinder;
import org.jbehave.core.junit.JUnitStories;
import org.jbehave.core.reporters.*;
import org.jbehave.core.steps.*;


/**
 * generic binder for all JBehave tests. Binds all the story files to the
 * step files
 *
 * @author testbuddy
 */
public class TestbuddyRunnerTest extends JUnitStories {

    private final CrossReference xref = new CrossReference();

    public TestbuddyRunnerTest() {
        configuredEmbedder().embedderControls().doGenerateViewAfterStories(false)
                .doIgnoreFailureInStories(false).doIgnoreFailureInView(true)
                .doVerboseFailures(true).useThreads(2).useStoryTimeouts("1500");
        configuredEmbedder().useEmbedderControls(new PropertyBasedEmbedderControls());
    }

    @Override
    public Configuration configuration() {
        if (super.hasConfiguration()) {
            return super.configuration();
        }
        return new MostUsefulConfiguration()
                .useStoryLoader(new LoadFromClasspath(this.getClass()))
                .useStoryReporterBuilder(new StoryReporterBuilder()
                        .withCodeLocation(CodeLocations.codeLocationFromClass(this.getClass()))
                        .withDefaultFormats().withPathResolver(new FilePrintStreamFactory.ResolveToPackagedName())
                        .withFormats(Format.CONSOLE, Format.TXT, Format.HTML)
                        .withCrossReference(new CrossReference())
                        .withRelativeDirectory("jbehave-reports")
                        .withFailureTraceCompression(true).withCrossReference(xref))
                .useParameterConverters(new ParameterConverters().
                        addConverters(new ParameterConverters.DateConverter(new SimpleDateFormat("yyyy-MM-dd")))) // use custom date pattern
                .useStepMonitor(new SilentStepMonitor());
    }

    @Override
    public InjectableStepsFactory stepsFactory() {
        ArrayList<Steps> stepFileList = new ArrayList<>();
        /*test-buddy modules - start*/
        /*test-buddy modules - end*/
        return new InstanceStepsFactory(configuration(), stepFileList);
    }

    protected List<String> storyPaths() {
        return new StoryFinder().findPaths(CodeLocations.codeLocationFromClass(this.getClass()),
                /*test-buddy stories - start*/
                Arrays.asList("**/*.story"),
                Arrays.asList(""));
                /*test-buddy stories - end*/
    }
}