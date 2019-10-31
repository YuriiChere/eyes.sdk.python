from __future__ import absolute_import

import typing

from applitools.common import EyesError, logger
from applitools.common.selenium import Configuration
from applitools.common.utils import argument_guard
from applitools.common.utils.general_utils import all_fields, proxy_to
from applitools.selenium import eyes_selenium_utils

from .fluent import Target
from .selenium_eyes import SeleniumEyes
from .visual_grid import VisualGridEyes, VisualGridRunner
from .webdriver import EyesWebDriver

if typing.TYPE_CHECKING:
    from typing import Text, Optional, Union, List, Tuple
    from selenium.webdriver.remote.webelement import WebElement
    from applitools.common import MatchResult, TestResults, Region, SessionType
    from applitools.common.utils.custom_types import (
        AnyWebDriver,
        ViewPort,
        FrameReference,
        AnyWebElement,
    )
    from applitools.core import (
        PositionProvider,
        FixedCutProvider,
        UnscaledFixedCutProvider,
        NullCutProvider,
    )
    from .frames import FrameChain
    from .fluent import SeleniumCheckSettings
    from .webelement import EyesWebElement


@proxy_to("configuration", all_fields(Configuration))
class Eyes(object):
    _is_visual_grid_eyes = False  # type: bool
    _visual_grid_eyes = None  # type: VisualGridEyes
    _selenium_eyes = None  # type: SeleniumEyes
    _runner = None  # type: Optional[VisualGridRunner]
    _driver = None  # type: Optional[EyesWebDriver]
    _is_opened = False  # type: bool

    def __init__(self, runner=None):
        # type: (Optional[VisualGridRunner]) -> None
        self._configuration = Configuration()  # type: Configuration

        # backward compatibility with settings server_url
        if isinstance(runner, str):
            self.configuration.server_url = runner
            runner = None

        if runner is None:
            self._selenium_eyes = SeleniumEyes(self)
        elif isinstance(runner, VisualGridRunner):
            self._runner = runner
            self._visual_grid_eyes = VisualGridEyes(runner, self)
            self._is_visual_grid_eyes = True
        else:
            raise ValueError("Wrong runner")

    @property
    def is_open(self):
        # type: () -> bool
        return self._is_opened

    def get_configuration(self):
        # type: () -> Configuration
        return self._configuration

    def set_configuration(self, configuration):
        # type: (Configuration) -> None
        argument_guard.is_a(configuration, Configuration)
        if self._configuration.api_key and not configuration.api_key:
            configuration.api_key = self._configuration.api_key
        if self._configuration.server_url and not configuration.server_url:
            configuration.server_url = self._configuration.server_url
        self._configuration = configuration

    configuration = property(get_configuration, set_configuration)

    @property
    def base_agent_id(self):
        # type: () -> Text
        """
        Must return version of SDK. (e.g. selenium, visualgrid) in next format:
            "eyes.{package}.python/{lib_version}"
        """
        return self._current_eyes.base_agent_id

    @property
    def full_agent_id(self):
        # type: () -> Text
        """
        Gets the agent id, which identifies the current library using the SDK.

        """
        return self._current_eyes.full_agent_id

    @property
    def should_stitch_content(self):
        # type: () -> bool
        return self._current_eyes.should_stitch_content

    @property
    def original_fc(self):
        # type: () -> Optional[FrameChain]
        """ Gets original frame chain

        Before check() call we save original frame chain

        Returns:
            Frame chain saved before check() call
        """
        return self._current_eyes.original_fc

    # def rotation(self):
    #     if not self._is_visual_grid_eyes:
    #         return self._selenium_eyes.rotation

    @property
    def device_pixel_ratio(self):
        # type: () -> int
        """
        Gets device pixel ratio.

        :return The device pixel ratio, or if the DPR is not known yet or if it wasn't
        possible to extract it.
        """
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes.device_pixel_ratio
        return 0

    @property
    def scale_ratio(self):
        # type: () -> float
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes.scale_ratio
        return 0

    @scale_ratio.setter
    def scale_ratio(self, value):
        # type: (float) -> None
        """
        Manually set the scale ratio for the images being validated.
        """
        if not self._is_visual_grid_eyes:
            self._selenium_eyes.scale_ratio = value

    @property
    def position_provider(self):
        """
        Sets position provider.
        """
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes.position_provider
        return None

    @property
    def _debug_screenshot_provided(self):
        # type: () -> bool
        """True if screenshots saving enabled."""
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes._debug_screenshot_provided

    @_debug_screenshot_provided.setter
    def _debug_screenshot_provided(self, save):
        # type: (bool) -> None
        if not self._is_visual_grid_eyes:
            self._selenium_eyes._debug_screenshot_provided = save

    @position_provider.setter
    def position_provider(self, provider):
        # type: (PositionProvider) -> None
        """
        Gets position provider.
        """
        if not self._is_visual_grid_eyes:
            self._selenium_eyes.position_provider = provider

    @property
    def cut_provider(self):
        # type:()->Optional[Union[FixedCutProvider,UnscaledFixedCutProvider,NullCutProvider]]
        """
        Gets current cut provider
        """
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes.cut_provider
        return None

    @cut_provider.setter
    def cut_provider(self, provider):
        # type: (Union[FixedCutProvider,UnscaledFixedCutProvider,NullCutProvider])->None
        """
        Manually set the the sizes to cut from an image before it's validated.

        :param provider:
        :return:
        """
        if not self._is_visual_grid_eyes:
            self._selenium_eyes.cut_provider = provider

    @property
    def is_cut_provider_explicitly_set(self):
        """
        Gets is cut provider explicitly set.
        """
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes.is_cut_provider_explicitly_set
        return False

    @property
    def agent_setup(self):
        """
        Gets agent setup.
        """
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes.agent_setup
        return None

    @property
    def current_frame_position_provider(self):
        # type: () -> Optional[PositionProvider]
        if not self._is_visual_grid_eyes:
            return self._selenium_eyes.current_frame_position_provider
        return None

    @staticmethod
    def get_viewport_size(driver):
        # type: (AnyWebDriver) -> ViewPort
        return eyes_selenium_utils.get_viewport_size_or_display_size(driver)

    @staticmethod
    def set_viewport_size(driver, size):
        # type: (AnyWebDriver, ViewPort) -> None
        assert driver is not None
        if size is None:
            raise ValueError("set_viewport_size require `size` parameter")
        eyes_selenium_utils.set_viewport_size(driver, size)

    def add_property(self, name, value):
        # type: (Text, Text) -> None
        """
        Associates a key/value pair with the test. This can be used later for filtering.
        :param name: (string) The property name.
        :param value: (string) The property value
        """
        self._current_eyes.add_property(name, value)

    def clear_properties(self):
        """
        Clears the list of custom properties.
        """
        self._current_eyes.clear_properties()

    def add_mouse_trigger_by_element(self, action, element):
        # type: (Text, AnyWebElement) -> None
        """
        Adds a mouse trigger.

        :param action: Mouse action (click, double click etc.)
        :param element: The element on which the action was performed.
        """
        if not self._is_visual_grid_eyes:
            self._selenium_eyes.add_mouse_trigger_by_element(action, element)

    def add_text_trigger_by_element(self, element, text):
        # type: (AnyWebElement, Text) -> None
        """
        Adds a text trigger.

        :param element: The element to which the text was sent.
        :param text: The trigger's text.
        """
        if not self._is_visual_grid_eyes:
            self._selenium_eyes.add_text_trigger_by_element(element, text)

    @property
    def driver(self):
        # type: () -> EyesWebDriver
        return self._driver

    @property
    def send_dom(self):
        # type: () -> bool
        if not self._is_visual_grid_eyes:
            return self.configuration.send_dom
        return False

    def check(self, name, check_settings):
        # type: (Text, SeleniumCheckSettings) -> MatchResult
        """
        Takes a snapshot and matches it with the expected output.

        :param name: The name of the tag.
        :param check_settings: target which area of the window to check.
        :return: The match results.
        """
        if self.configuration.is_disabled:
            return MatchResult()
        if not self.is_open:
            self.abort()
            raise EyesError("you must call open() before checking")
        return self._current_eyes.check(name, check_settings)

    def check_window(self, tag=None, match_timeout=-1, fully=False):
        # type: (Optional[Text], int, bool) -> MatchResult
        """
        Takes a snapshot of the application under test and matches it with the expected
         output.

        :param tag: An optional tag to be associated with the snapshot.
        :param match_timeout:  The amount of time to retry matching (milliseconds)
        :param fully: Defines that the screenshot will contain the entire window.
        :return: The match results.
        """
        logger.debug("check_window('%s')" % tag)
        return self.check(tag, Target.window().timeout(match_timeout).fully(fully))

    def check_frame(self, frame_reference, tag=None, match_timeout=-1, fully=False):
        # type: (FrameReference, Optional[Text], int, bool) -> MatchResult
        """
        Check frame.

        :param frame_reference: The name or id of the frame to check. (The same
                name/id as would be used in a call to driver.switch_to.frame()).
        :param tag: An optional tag to be associated with the match.
        :param match_timeout: The amount of time to retry matching. (Milliseconds)
        :param fully: Defines that the screenshot will contain the entire frame.
        :return: The match results.
        """
        return self.check(tag, Target.frame(frame_reference).timeout(match_timeout))

    def check_region(
        self,
        region,  # type: Union[Region,Text,List,Tuple,WebElement,EyesWebElement]
        tag=None,  # type: Optional[Text]
        match_timeout=-1,  # type: int
        stitch_content=False,  # type: bool
    ):
        # type: (...) -> MatchResult
        """
        Takes a snapshot of the given region from the browser using the web driver
        and matches it with the expected output. If the current context is a frame,
        the region is offsetted relative to the frame.

        :param region: The region which will be visually validated. The coordinates are
                       relative to the viewport of the current frame.
        :param tag: Description of the visual validation checkpoint.
        :param match_timeout: Timeout for the visual validation checkpoint
                              (milliseconds).
        :param stitch_content: If `True`, stitch the internal content of the region
        :return: The match results.
        """
        return self.check(
            tag,
            Target.region(region).timeout(match_timeout).stitch_content(stitch_content),
        )

    def check_region_in_frame(
        self,
        frame_reference,  # type: FrameReference
        region,  # type: Union[Region,Text,List,Tuple,WebElement,EyesWebElement]
        tag=None,  # type: Optional[Text]
        match_timeout=-1,  # type: int
        stitch_content=False,  # type: bool
    ):
        # type: (...) -> MatchResult
        """
        Checks a region within a frame, and returns to the current frame.

        :param frame_reference: A reference to the frame in which the region
                                should be checked.
        :param region: Specifying the region to check inside the frame.
        :param tag: Description of the visual validation checkpoint.
        :param match_timeout: Timeout for the visual validation checkpoint
                              (milliseconds).
        :param stitch_content: If `True`, stitch the internal content of the region
        :return: None
        """
        # TODO: remove this disable
        if self.configuration.is_disabled:
            logger.info("check_region_in_frame_by_selector(): ignored (disabled)")
            return MatchResult()
        logger.debug("check_region_in_frame_by_selector('%s')" % tag)
        return self.check(
            tag,
            Target.region(region)
            .frame(frame_reference)
            .stitch_content(stitch_content)
            .timeout(match_timeout),
        )

    def open(
        self,
        driver,  # type: AnyWebDriver
        app_name=None,  # type: Optional[Text]
        test_name=None,  # type: Optional[Text]
        viewport_size=None,  # type: Optional[ViewPort]
    ):
        # type: (...) -> EyesWebDriver
        """
        Starts a test.

        :param driver: The driver that controls the browser hosting the application
            under the test.
        :param app_name: The name of the application under test.
        :param test_name: The test name.
        :param viewport_size: The client's viewport size (i.e.,
            the visible part of the document's body) or None to allow any viewport size.
        :raise EyesError: If the session was already open.
        """
        if app_name:
            self.configuration.app_name = app_name
        if test_name:
            self.configuration.test_name = test_name
        if viewport_size:
            self.configuration.viewport_size = viewport_size  # type: ignore
        self._init_driver(driver)
        result = self._current_eyes.open(self.driver)
        self._is_opened = True
        return result

    def close(self, raise_ex=True):
        # type: (bool) -> Optional[TestResults]
        """
        Ends the test.

        :param raise_ex: If true, an exception will be raised for failed/new tests.
        :return: The test results.
        """
        result = self._current_eyes.close(raise_ex)
        self._is_opened = False
        return result

    def close_async(self):
        if self._is_visual_grid_eyes:
            self._visual_grid_eyes.close_async()
        else:
            self._selenium_eyes.close(False)

    def abort(self):
        """
        If a test is running, aborts it. Otherwise, does nothing.
        """
        self._current_eyes.abort()

    def abort_if_not_closed(self):
        logger.deprecation("Use `abort()` instead")
        self.abort()

    def _init_driver(self, driver):
        # type: (AnyWebDriver) -> None
        if isinstance(driver, EyesWebDriver):
            # If the driver is an EyesWebDriver (as might be the case when tests are ran
            # consecutively using the same driver object)
            self._driver = driver
        else:
            self._driver = EyesWebDriver(driver, self)

    @property
    def _current_eyes(self):
        # type: () -> Union[SeleniumEyes, VisualGridEyes]
        if self._is_visual_grid_eyes:
            return self._visual_grid_eyes
        else:
            return self._selenium_eyes

    @property
    def _original_scroll_position(self):
        if self._selenium_eyes:
            return self._selenium_eyes._original_scroll_position
        return None
