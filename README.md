# SNOM Endpoint Module for Open Paging Server

PopUp Config:

1. Log into the phone's web configuration interface.
2. Navigate to **Advanced** -> **QoS/Security**.
3. Under the **HTTP server** section, apply the following changes:
   * Set **Authentication Scheme** to `BASIC`.
   * Set **Restrict URI Queries** to `OFF`.
   * Set **Use Hidden Tags** to `OFF`.
4. In Open Paging Server (OPS), navigate to the phone's endpoint settings and enter the **HTTP Server username and password** you set on the phone.
5. Add the phone's **IP address** into OPS.

Multicast Config:
1) Create a Multicast group inside of open paging server
2) Login to the phone's web configuration utility
3) Go into Advanced -> SIP/RTP
4) Enable Multicast Support
5) Under Zone 1 add in a name, and add in the multicast address you made in open paging server


## Demo
[![Watch the Video](https://img.youtube.com/vi/F06C0dwH6a8/hqdefault.jpg)](https://youtube.com/shorts/F06C0dwH6a8)


## Roadmap
### KEY:
✅Accomplished
➖In Progress
❌Not done yet

### Roadmap
❌Image Popups for supported phones 

  Note: Figuring out how to get descriptions to work when using images, as SNOM tends to only allow images when sending a image message

❌Open Paging Server App for SNOM Phones

  Note: This app will let you send messages from a visual menu using the SNOM apps features

> 💡 **Have a feature request?** Please open a [Feature Request issue](https://github.com/OpenPagingServer/snom/issues)!

## Contributing
Contributions to this module whether it is for fixing bugs, or adding new features is welcomed! If you would like to contribute, feel free to do so, and open a pull request.

Pull Request Requirements:
1. **Brief Description:** A short summary of what the PR changes.
2. **Detailed Description:** A detailed breakdown explaining *what* was done, *where* the changes were made, and *why* they are necessary/ or why they were done.
