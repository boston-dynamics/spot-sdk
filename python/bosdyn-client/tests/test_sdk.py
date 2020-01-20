import pkg_resources
import unittest

import bosdyn.client
import bosdyn.client.processors


class ServiceClientMock(bosdyn.client.BaseClient):
    default_authority = 'the-knights-of-ni'
    default_service_name = 'mock'
    service_type = 'bosdyn.api.Mock'

    def __init__(self):
        super(ServiceClientMock, self).__init__(lambda channel: None)


class ClientTest(unittest.TestCase):
    def test_constructors(self):
        client = bosdyn.client.BaseClient(lambda channel: None)
        self.assertEqual(len(client.request_processors), 0)
        self.assertEqual(len(client.response_processors), 0)


class SdkTest(unittest.TestCase):
    CA_CERT = """-----BEGIN CERTIFICATE-----
Lovely Spam! Wonderful Spam!
Lovely Spam! Wonderful Spam
Spa-a-a-a-a-a-a-am
Spa-a-a-a-a-a-a-am
Spa-a-a-a-a-a-a-am
Spa-a-a-a-a-a-a-am
Lovely Spam! (Lovely Spam!)
Lovely Spam! (Lovely Spam!)
Lovely Spam!
Spam, Spam, Spam, Spam!
-----END CERTIFICATE-----""".encode()

    def _create_sdk(self, client_name='sdk-test', app_token='ABC123', cert=None):
        sdk = bosdyn.client.Sdk()
        sdk.client_name = client_name
        sdk.app_token = app_token
        sdk.cert = cert or SdkTest.CA_CERT
        return sdk

    def _create_secure_channel(self, robot, port=54321, authority='null.spot.robot'):
        return robot.create_secure_channel(port, authority)

    def _create_robot(self, sdk, nickname='my-robot-name', address='no-address'):
        robot = sdk.create_robot(address, nickname)
        return robot

    def test_robot_creation(self):
        sdk = self._create_sdk()

        # Takes the place of a processor.
        request_p = object()
        response_p = object()
        sdk.request_processors.append(request_p)
        sdk.response_processors.append(response_p)

        robot = self._create_robot(sdk, 'test-robot')
        self.assertIn(request_p, robot.request_processors)
        self.assertIn(response_p, robot.response_processors)
        self.assertNotIn(request_p, robot.response_processors)
        self.assertNotIn(response_p, robot.request_processors)

    def test_robot_creation_without_app_token(self):
        sdk = self._create_sdk(app_token=None)

        # Takes the place of a processor.
        request_p = object()
        response_p = object()
        sdk.request_processors.append(request_p)
        sdk.response_processors.append(response_p)

        with self.assertRaises(bosdyn.client.sdk.UnsetAppTokenError):
            robot = self._create_robot(sdk, 'test-robot')

    def test_client_name_propogation(self):
        sdk = self._create_sdk()
        sdk.request_processors.append(bosdyn.client.processors.AddRequestHeader(lambda: sdk.client_name))
        robot = self._create_robot(sdk, 'test-robot')
        sdk.client_name = 'changed-my-mind'

        found_header_processor = False
        for proc in robot.request_processors:
            if isinstance(proc, bosdyn.client.processors.AddRequestHeader):
                self.assertEqual(sdk.client_name, proc.get_client_name())
                found_header_processor = True
        self.assertTrue(found_header_processor)

    def test_client_creation(self):
        service_name = ServiceClientMock.default_service_name
        service_type = ServiceClientMock.default_service_name
        sdk = self._create_sdk()
        robot = self._create_robot(sdk, 'test-robot')
        # This should raise an exception -- we haven't installed a factory for the service.
        with self.assertRaises(KeyError):
            client = robot.ensure_client(service_name)
        # Register the ServiceClientMock constructor as the function to call for the service.
        robot.service_type_by_name[service_name] = service_type
        robot.service_client_factories_by_type[service_type] = ServiceClientMock
        client = robot.ensure_client(service_name)

    def test_load_robot_cert(self):
        sdk = bosdyn.client.Sdk()
        sdk.load_robot_cert()
        self.assertEqual(sdk.cert, pkg_resources.resource_stream('bosdyn.client.resources', 'robot.pem').read())
        with self.assertRaises(IOError):
            sdk.load_robot_cert('this-path-does-not-exist')


    def test_load_app_token(self):
        sdk = bosdyn.client.Sdk()

        with self.assertRaises(bosdyn.client.sdk.UnableToLoadAppTokenError):
            sdk.load_app_token('invalid')

        with self.assertRaises(bosdyn.client.sdk.UnsetAppTokenError):
            sdk.load_app_token(None)


if __name__ == '__main__':
    unittest.main()
